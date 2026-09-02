import pytest
import httpx
from app.main import app

@pytest.fixture
async def async_client():
    """Async HTTP client fixture for FastAPI endpoint testing."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client
