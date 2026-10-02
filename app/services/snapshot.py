import asyncio
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.config import (
    REST_API_URL,
    BASE_URL,
    GCS_BUCKET_NAME,
    SNAPSHOT_FILE_NAME,
    LOCAL_CACHE_DIR,
    SNAPSHOT_MAX_PAGES,
    SNAPSHOT_ITEMS_PER_PAGE,
    SNAPSHOT_AUTO_REFRESH_SECONDS,
)
from app.models import ReleaseItem, SearchResponse, CatalogSnapshot, SnapshotStatus
from app.services.parser import parse_title
from app.services.scraper import get_http_client, get_movie_poster

logger = logging.getLogger("bhilaitv.snapshot")

# Global In-Memory Snapshot Cache
_ACTIVE_SNAPSHOT: Optional[CatalogSnapshot] = None
_SYNC_LOCK = asyncio.Lock()
_BACKGROUND_WORKER_TASK: Optional[asyncio.Task] = None
_IS_SYNCING: bool = False
_LAST_STORAGE_BACKEND: str = "none"


def get_active_snapshot() -> Optional[CatalogSnapshot]:
    """Returns the current in-memory CatalogSnapshot if loaded."""
    return _ACTIVE_SNAPSHOT


def is_snapshot_ready() -> bool:
    """Returns True if the snapshot is loaded and contains releases."""
    return _ACTIVE_SNAPSHOT is not None and len(_ACTIVE_SNAPSHOT.releases) > 0


def get_snapshot_slice(page: int = 1, per_page: int = 20) -> Optional[SearchResponse]:
    """
    Sub-millisecond retrieval of releases from the in-memory snapshot.
    If the requested slice falls within the snapshot's covered range,
    returns a SearchResponse directly from RAM.
    Otherwise returns None, allowing the caller to fall back to live scraping.
    """
    snapshot = _ACTIVE_SNAPSHOT
    if snapshot is None or not snapshot.releases:
        return None

    if page < 1 or per_page < 1:
        return None

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Check if start index is beyond cached items
    if start_idx >= len(snapshot.releases):
        return None

    slice_items = snapshot.releases[start_idx:end_idx]
    if not slice_items:
        return None

    # Calculate accurate total pages based on requested per_page
    total_count = snapshot.total_count
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    return SearchResponse(
        results=slice_items,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        query=None
    )


def _save_to_local_cache(json_str: str) -> None:
    """Helper to write snapshot data to local cache file."""
    try:
        LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        target = LOCAL_CACHE_DIR / SNAPSHOT_FILE_NAME
        target.write_text(json_str, encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not write snapshot to local cache directory: {e}")


def load_snapshot() -> bool:
    """
    Loads snapshot into memory.
    Priority 1: Google Cloud Storage (if GCS_BUCKET_NAME is configured).
    Priority 2: Local filesystem cache fallback.
    Returns True if successfully hydrated, False otherwise.
    """
    global _ACTIVE_SNAPSHOT, _LAST_STORAGE_BACKEND

    # 1. Attempt GCS load
    if GCS_BUCKET_NAME:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(SNAPSHOT_FILE_NAME)
            if blob.exists():
                data_str = blob.download_as_text()
                snapshot = CatalogSnapshot.model_validate_json(data_str)
                _ACTIVE_SNAPSHOT = snapshot
                _LAST_STORAGE_BACKEND = f"gs://{GCS_BUCKET_NAME}/{SNAPSHOT_FILE_NAME}"
                _save_to_local_cache(data_str)
                logger.info(
                    f"[SNAPSHOT] Hydrated from GCS ({len(snapshot.releases)} releases, "
                    f"{snapshot.pages_cached} pages, age: {time.time() - snapshot.generated_at:.1f}s)"
                )
                return True
            else:
                logger.info(f"[SNAPSHOT] Blob gs://{GCS_BUCKET_NAME}/{SNAPSHOT_FILE_NAME} does not exist yet.")
        except Exception as e:
            logger.warning(f"[SNAPSHOT] Failed to read from GCS bucket '{GCS_BUCKET_NAME}': {e}")

    # 2. Attempt Local Cache load
    local_file = LOCAL_CACHE_DIR / SNAPSHOT_FILE_NAME
    if local_file.is_file():
        try:
            data_str = local_file.read_text(encoding="utf-8")
            snapshot = CatalogSnapshot.model_validate_json(data_str)
            _ACTIVE_SNAPSHOT = snapshot
            _LAST_STORAGE_BACKEND = f"local://{local_file}"
            logger.info(
                f"[SNAPSHOT] Hydrated from local cache ({len(snapshot.releases)} releases, "
                f"age: {time.time() - snapshot.generated_at:.1f}s)"
            )
            return True
        except Exception as e:
            logger.warning(f"[SNAPSHOT] Failed to read local cache file '{local_file}': {e}")

    return False


def save_snapshot(snapshot: CatalogSnapshot) -> bool:
    """
    Persists a CatalogSnapshot to GCS and local cache, then updates in-memory cache.
    """
    global _ACTIVE_SNAPSHOT, _LAST_STORAGE_BACKEND

    payload = snapshot.model_dump_json(indent=2)

    # 1. Persist to local cache
    _save_to_local_cache(payload)
    _LAST_STORAGE_BACKEND = f"local://{LOCAL_CACHE_DIR / SNAPSHOT_FILE_NAME}"

    # 2. Persist to GCS if configured
    if GCS_BUCKET_NAME:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(SNAPSHOT_FILE_NAME)
            blob.upload_from_string(payload, content_type="application/json")
            _LAST_STORAGE_BACKEND = f"gs://{GCS_BUCKET_NAME}/{SNAPSHOT_FILE_NAME}"
            logger.info(f"[SNAPSHOT] Persisted to GCS: gs://{GCS_BUCKET_NAME}/{SNAPSHOT_FILE_NAME}")
        except Exception as e:
            logger.error(f"[SNAPSHOT] Failed to upload snapshot to GCS: {e}")

    # 3. Swap in-memory reference
    _ACTIVE_SNAPSHOT = snapshot
    return True


async def _fetch_single_page(client, page: int, per_page: int, sem: asyncio.Semaphore) -> tuple[int, int, List[ReleaseItem]]:
    """Fetches a single page with concurrency throttled by semaphore."""
    async with sem:
        params = {
            "page": page,
            "per_page": per_page,
            "_fields": "id,date,modified,slug,title,link"
        }
        url = f"{REST_API_URL}/posts"
        resp = await client.get(url, params=params)
        resp.raise_for_status()

        total_count = int(resp.headers.get("X-WP-Total", 0))
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        data = resp.json()

        items = []
        for post in data:
            raw_title = post.get("title", {}).get("rendered", "")
            items.append(ReleaseItem(
                id=post["id"],
                raw_title=raw_title,
                parsed=parse_title(raw_title),
                date=post.get("date", ""),
                slug=post.get("slug", ""),
                url=post.get("link", f"{BASE_URL}/archives/{post['id']}/")
            ))
        return total_count, total_pages, items


async def build_catalog_snapshot(
    max_pages: int = SNAPSHOT_MAX_PAGES,
    per_page: int = SNAPSHOT_ITEMS_PER_PAGE
) -> CatalogSnapshot:
    """
    Fetches the top `max_pages` concurrently from upstream WordPress,
    resolves/enriches posters, constructs a CatalogSnapshot, and persists it.
    """
    logger.info(f"[SNAPSHOT] Initiating snapshot build for top {max_pages} pages ({per_page} per page)...")
    client = await get_http_client()
    sem = asyncio.Semaphore(5)

    # 1. Concurrently fetch all pages
    tasks = [_fetch_single_page(client, p, per_page, sem) for p in range(1, max_pages + 1)]
    page_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items: List[ReleaseItem] = []
    seen_ids = set()
    total_upstream_count = 0
    total_upstream_pages = 1

    for idx, res in enumerate(page_results, start=1):
        if isinstance(res, Exception):
            logger.warning(f"[SNAPSHOT] Error fetching page {idx}: {res}")
            continue
        tot_cnt, tot_pgs, items = res
        if tot_cnt > total_upstream_count:
            total_upstream_count = tot_cnt
            total_upstream_pages = tot_pgs
        for it in items:
            if it.id not in seen_ids:
                seen_ids.add(it.id)
                all_items.append(it)

    logger.info(f"[SNAPSHOT] Scraped {len(all_items)} unique items across {max_pages} pages. Enriching posters...")

    # 2. Enrich posters concurrently in chunks of 25 to avoid overwhelming CDN rate limits
    chunk_size = 25
    for i in range(0, len(all_items), chunk_size):
        chunk = all_items[i:i + chunk_size]
        titles = [it.parsed.clean_title for it in chunk]
        posters = await asyncio.gather(*[get_movie_poster(t) for t in titles], return_exceptions=True)
        for it, p in zip(chunk, posters):
            if isinstance(p, str) and p:
                it.poster_url = p

    # 3. Assemble Snapshot
    now = time.time()
    iso_now = datetime.now(timezone.utc).isoformat()
    snapshot = CatalogSnapshot(
        generated_at=now,
        iso_date=iso_now,
        total_count=total_upstream_count,
        total_pages=total_upstream_pages,
        pages_cached=max_pages,
        items_per_page=per_page,
        releases=all_items
    )

    # 4. Save and return
    save_snapshot(snapshot)
    logger.info(
        f"[SNAPSHOT] Catalog snapshot build complete: {len(all_items)} releases cached. "
        f"Backend: {_LAST_STORAGE_BACKEND}"
    )
    return snapshot


async def sync_snapshot(force: bool = False) -> CatalogSnapshot:
    """
    Synchronizes the snapshot: fetches upstream, enriches posters, and saves.
    Ensures only one sync runs at a time via _SYNC_LOCK.
    """
    global _IS_SYNCING
    if _IS_SYNCING and not force:
        logger.info("[SNAPSHOT] Sync already in progress, skipping duplicate invocation.")
        if _ACTIVE_SNAPSHOT is not None:
            return _ACTIVE_SNAPSHOT

    async with _SYNC_LOCK:
        _IS_SYNCING = True
        try:
            snapshot = await build_catalog_snapshot()
            return snapshot
        finally:
            _IS_SYNCING = False


async def _snapshot_refresh_loop():
    """Background loop that periodically re-syncs the snapshot."""
    logger.info(f"[SNAPSHOT] Background refresh loop started (interval: {SNAPSHOT_AUTO_REFRESH_SECONDS}s).")
    while True:
        try:
            await asyncio.sleep(SNAPSHOT_AUTO_REFRESH_SECONDS)
            logger.info("[SNAPSHOT] Executing scheduled catalog snapshot refresh...")
            await sync_snapshot()
        except asyncio.CancelledError:
            logger.info("[SNAPSHOT] Background refresh loop stopped.")
            break
        except Exception as e:
            logger.error(f"[SNAPSHOT] Error in scheduled refresh: {e}")
            await asyncio.sleep(60)


async def init_snapshot():
    """
    Lifecycle hook called on application startup.
    Tries to hydrate from GCS / local file immediately.
    If not available, triggers an asynchronous background sync.
    Starts the periodic refresh worker.
    """
    global _BACKGROUND_WORKER_TASK

    loaded = load_snapshot()
    if not loaded:
        logger.info("[SNAPSHOT] No pre-existing snapshot found. Triggering initial build in background...")
        asyncio.create_task(sync_snapshot())

    if _BACKGROUND_WORKER_TASK is None or _BACKGROUND_WORKER_TASK.done():
        _BACKGROUND_WORKER_TASK = asyncio.create_task(_snapshot_refresh_loop())


async def stop_snapshot_worker():
    """Lifecycle hook called on application shutdown."""
    global _BACKGROUND_WORKER_TASK
    if _BACKGROUND_WORKER_TASK and not _BACKGROUND_WORKER_TASK.done():
        _BACKGROUND_WORKER_TASK.cancel()
        try:
            await _BACKGROUND_WORKER_TASK
        except asyncio.CancelledError:
            pass


def get_snapshot_status() -> SnapshotStatus:
    """Returns current runtime status of the snapshot engine."""
    snapshot = _ACTIVE_SNAPSHOT
    if snapshot is None:
        return SnapshotStatus(
            ready=False,
            total_items=0,
            pages_cached=0,
            total_upstream_items=0,
            total_upstream_pages=0,
            generated_at=None,
            iso_date=None,
            age_seconds=None,
            storage_backend=_LAST_STORAGE_BACKEND,
            is_syncing=_IS_SYNCING
        )

    now = time.time()
    return SnapshotStatus(
        ready=True,
        total_items=len(snapshot.releases),
        pages_cached=snapshot.pages_cached,
        total_upstream_items=snapshot.total_count,
        total_upstream_pages=snapshot.total_pages,
        generated_at=snapshot.generated_at,
        iso_date=snapshot.iso_date,
        age_seconds=round(now - snapshot.generated_at, 2),
        storage_backend=_LAST_STORAGE_BACKEND,
        is_syncing=_IS_SYNCING
    )
