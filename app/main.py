from fastapi import FastAPI, Query, HTTPException, Path as FastPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
import logging

from app.models import SearchResponse, ReleaseDetail, SnapshotStatus
from app.services.scraper import fetch_latest_releases, search_releases, fetch_release_detail, resolve_hubcloud_direct_links, get_movie_poster
from app.services.snapshot import (
    init_snapshot,
    stop_snapshot_worker,
    get_snapshot_slice,
    get_snapshot_status,
    sync_snapshot,
    is_snapshot_ready,
)
from app.config import SNAPSHOT_SYNC_KEY

from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bhilaitv")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize snapshot engine (hydrates from GCS/local cache, starts background refresh)
    await init_snapshot()
    yield
    await stop_snapshot_worker()
    from app.services.scraper import close_http_client
    await close_http_client()

app = FastAPI(
    title="BhilaiTV // Terminal Movie Explorer",
    description="High-speed Terminal-themed Live Movie & Series Explorer powered by FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Mount static directory
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/api/health")
async def health():
    return {
        "status": "ONLINE",
        "service": "BhilaiTV Backend",
        "version": "1.0.0",
        "snapshot_ready": is_snapshot_ready()
    }

@app.get("/api/snapshot/status", response_model=SnapshotStatus)
async def snapshot_status():
    """Returns real-time status of the 20-page catalog snapshot in memory & GCS."""
    return get_snapshot_status()

@app.api_route("/api/snapshot/sync", methods=["GET", "POST"])
async def trigger_snapshot_sync(key: Optional[str] = Query(None)):
    """
    Manually triggers or schedules a full rebuild of the 20-page catalog snapshot.
    Protected by SNAPSHOT_SYNC_KEY if configured.
    """
    if SNAPSHOT_SYNC_KEY and key != SNAPSHOT_SYNC_KEY:
        raise HTTPException(status_code=403, detail="Invalid snapshot sync authorization key")
    
    # Run sync
    snapshot = await sync_snapshot(force=True)
    return {
        "status": "SUCCESS",
        "message": f"Successfully synchronized {len(snapshot.releases)} releases across {snapshot.pages_cached} pages",
        "snapshot": get_snapshot_status()
    }

@app.get("/api/latest", response_model=SearchResponse)
async def get_latest(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=50)):
    try:
        # Tier 1: In-memory snapshot cache for pages 1-20 (sub-millisecond latency, zero upstream load)
        snapshot_slice = get_snapshot_slice(page=page, per_page=per_page)
        if snapshot_slice is not None:
            return snapshot_slice

        # Tier 2: Real-time scraping fallback (for deep pagination >20 or cold cache)
        return await fetch_latest_releases(page=page, per_page=per_page)
    except Exception as e:
        logger.error(f"Error fetching latest releases: {e}")
        raise HTTPException(status_code=502, detail=f"Upstream provider error: {str(e)}")

@app.get("/api/search", response_model=SearchResponse)
async def search(q: str = Query(..., min_length=1), page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=50)):
    try:
        return await search_releases(query=q, page=page, per_page=per_page)
    except Exception as e:
        logger.error(f"Error searching releases for '{q}': {e}")
        raise HTTPException(status_code=502, detail=f"Upstream provider error: {str(e)}")

@app.get("/api/release/{post_id}", response_model=ReleaseDetail)
async def get_release(post_id: int = FastPath(..., ge=1, description="Post ID must be greater than 0")):
    try:
        return await fetch_release_detail(post_id=post_id)
    except Exception as e:
        logger.error(f"Error fetching release detail for ID {post_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Release not found or unable to parse: {str(e)}")

@app.get("/api/poster")
async def get_poster(title: str = Query(..., min_length=1)):
    try:
        poster_url = await get_movie_poster(title)
        return {"title": title, "poster_url": poster_url}
    except Exception as e:
        logger.error(f"Error retrieving poster for '{title}': {e}")
        return {"title": title, "poster_url": None}

@app.get("/api/resolve/direct")
async def resolve_direct_link(url: str = Query(..., min_length=5)):
    try:
        return await resolve_hubcloud_direct_links(hubcloud_url=url)
    except Exception as e:
        logger.error(f"Error resolving direct download link for '{url}': {e}")
        raise HTTPException(status_code=502, detail=f"Failed to resolve direct download stream: {str(e)}")

@app.get("/api/resolve/gdflix")
async def resolve_gdflix_direct(url: str = Query(..., min_length=5)):
    """
    Uses curl_cffi Chrome TLS impersonation to bypass Cloudflare Turnstile on GDFlix
    and extract the FastCloud / ZipDisk resumable direct stream with fallbacks.
    """
    try:
        from app.services.gdflix_resolver import resolve_gdflix_instant
        result = await resolve_gdflix_instant(gdflix_url=url)
        if not result.get("direct_url"):
            raise HTTPException(status_code=422, detail="No direct download stream found on this GDFlix page")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving GDFlix link for '{url}': {e}")
        raise HTTPException(status_code=502, detail=f"GDFlix resolver error: {str(e)}")
