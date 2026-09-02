import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ONLINE"
        assert "version" in data

@pytest.mark.asyncio
async def test_latest_releases_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/latest?page=1&per_page=10")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert "total_count" in data
        assert len(data["results"]) > 0

@pytest.mark.asyncio
async def test_search_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/search?q=ozark&page=1&per_page=5")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert len(data["results"]) > 0

@pytest.mark.asyncio
async def test_resolve_hubcloud_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        url = "https://hubcloud.cx/drive/p8f228fystpt10e"
        r = await client.get(f"/api/resolve/direct?url={url}")
        assert r.status_code == 200
        data = r.json()
        assert "direct_links" in data
        assert len(data["direct_links"]) > 0

@pytest.mark.asyncio
async def test_resolve_gdflix_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        url = "https://new3.gdflix.io/file/ekmvapISgHELLR7"
        r = await client.get(f"/api/resolve/gdflix?url={url}")
        assert r.status_code == 200
        data = r.json()
        assert data.get("direct_url") is not None
