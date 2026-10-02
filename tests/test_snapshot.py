import pytest
import time
from pathlib import Path
from app.models import CatalogSnapshot, ReleaseItem, ParsedTitleInfo, SearchResponse
from app.services import snapshot as snap_module
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import SNAPSHOT_SYNC_KEY

@pytest.fixture(autouse=True)
def reset_snapshot_state():
    """Resets snapshot module state between tests."""
    orig_snap = snap_module._ACTIVE_SNAPSHOT
    orig_backend = snap_module._LAST_STORAGE_BACKEND
    yield
    snap_module._ACTIVE_SNAPSHOT = orig_snap
    snap_module._LAST_STORAGE_BACKEND = orig_backend

def create_dummy_snapshot(num_items: int = 50, pages_cached: int = 5) -> CatalogSnapshot:
    releases = []
    for i in range(1, num_items + 1):
        releases.append(ReleaseItem(
            id=1000 + i,
            raw_title=f"Sample Test Movie {i} 2024 1080p Web-DL",
            parsed=ParsedTitleInfo(
                clean_title=f"Sample Test Movie {i}",
                year="2024",
                quality="1080p",
                size="1.2GB",
                is_series=False
            ),
            date="2026-09-01 12:00:00",
            slug=f"sample-test-movie-{i}",
            url=f"https://abhilinks.site/archives/{1000 + i}/",
            poster_url=f"https://m.media-amazon.com/images/M/poster_{i}.jpg"
        ))
    return CatalogSnapshot(
        generated_at=time.time(),
        iso_date="2026-10-02T00:00:00Z",
        total_count=1200,
        total_pages=120,
        pages_cached=pages_cached,
        items_per_page=10,
        releases=releases
    )

def test_snapshot_slicing_empty():
    snap_module._ACTIVE_SNAPSHOT = None
    assert snap_module.get_snapshot_slice(1, 20) is None
    assert snap_module.is_snapshot_ready() is False

def test_snapshot_slicing_valid():
    dummy = create_dummy_snapshot(num_items=40, pages_cached=4)
    snap_module._ACTIVE_SNAPSHOT = dummy
    assert snap_module.is_snapshot_ready() is True

    # Page 1, 10 per page
    res_p1 = snap_module.get_snapshot_slice(page=1, per_page=10)
    assert res_p1 is not None
    assert len(res_p1.results) == 10
    assert res_p1.results[0].id == 1001
    assert res_p1.results[-1].id == 1010
    assert res_p1.total_count == 1200
    assert res_p1.total_pages == 120
    assert res_p1.current_page == 1

    # Page 2, 10 per page
    res_p2 = snap_module.get_snapshot_slice(page=2, per_page=10)
    assert res_p2 is not None
    assert len(res_p2.results) == 10
    assert res_p2.results[0].id == 1011

    # Page 4, 10 per page (last cached page)
    res_p4 = snap_module.get_snapshot_slice(page=4, per_page=10)
    assert res_p4 is not None
    assert len(res_p4.results) == 10
    assert res_p4.results[-1].id == 1040

    # Page 5 (beyond 40 items cached) -> should return None to trigger upstream fallback
    res_p5 = snap_module.get_snapshot_slice(page=5, per_page=10)
    assert res_p5 is None

    # Invalid pagination
    assert snap_module.get_snapshot_slice(page=0, per_page=10) is None
    assert snap_module.get_snapshot_slice(page=1, per_page=0) is None

def test_snapshot_local_cache_roundtrip(tmp_path: Path, monkeypatch):
    """Verifies saving and loading from local file cache."""
    test_file = "test_snapshot.json"
    monkeypatch.setattr(snap_module, "LOCAL_CACHE_DIR", tmp_path)
    monkeypatch.setattr(snap_module, "SNAPSHOT_FILE_NAME", test_file)
    monkeypatch.setattr(snap_module, "GCS_BUCKET_NAME", "")  # disable GCS for this test

    dummy = create_dummy_snapshot(num_items=15, pages_cached=2)
    snap_module.save_snapshot(dummy)

    # Verify file was written on disk
    saved_file = tmp_path / test_file
    assert saved_file.is_file()

    # Clear memory and reload from disk
    snap_module._ACTIVE_SNAPSHOT = None
    loaded = snap_module.load_snapshot()
    assert loaded is True
    assert snap_module._ACTIVE_SNAPSHOT is not None
    assert len(snap_module._ACTIVE_SNAPSHOT.releases) == 15
    assert snap_module._ACTIVE_SNAPSHOT.releases[0].id == 1001

@pytest.mark.asyncio
async def test_snapshot_api_endpoints():
    """Tests /api/snapshot/status and /api/latest with in-memory snapshot."""
    dummy = create_dummy_snapshot(num_items=30, pages_cached=3)
    snap_module._ACTIVE_SNAPSHOT = dummy
    snap_module._LAST_STORAGE_BACKEND = "test_memory"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check status endpoint
        resp = await client.get("/api/snapshot/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True
        assert data["total_items"] == 30
        assert data["pages_cached"] == 3
        assert data["total_upstream_items"] == 1200
        assert data["storage_backend"] == "test_memory"

        # Check /api/latest serves from snapshot
        resp_latest = await client.get("/api/latest?page=1&per_page=10")
        assert resp_latest.status_code == 200
        latest_data = resp_latest.json()
        assert len(latest_data["results"]) == 10
        assert latest_data["results"][0]["id"] == 1001

        # Check /api/snapshot/sync unauthorized
        resp_sync_unauth = await client.post("/api/snapshot/sync?key=wrong_key")
        assert resp_sync_unauth.status_code == 403

        # Check /api/health includes snapshot_ready
        resp_health = await client.get("/api/health")
        assert resp_health.status_code == 200
        assert resp_health.json()["snapshot_ready"] is True
