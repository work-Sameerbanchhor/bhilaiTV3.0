import pytest
from app.services.scraper import resolve_hubcloud_direct_links
from app.services.gdflix_resolver import resolve_gdflix_instant

@pytest.mark.asyncio
async def test_hubcloud_resolver_live():
    # Test a real HubCloud link from active catalog
    hubcloud_url = "https://hubcloud.cx/drive/p8f228fystpt10e"
    result = await resolve_hubcloud_direct_links(hubcloud_url)
    
    assert "source_url" in result
    assert "direct_links" in result
    assert len(result["direct_links"]) > 0
    
    # Check that at least one direct stream was extracted
    types = [dl["type"] for dl in result["direct_links"]]
    assert any("r2" in t or "direct" in t or "10gbps" in t for t in types)

@pytest.mark.asyncio
async def test_gdflix_fastcloud_resolver_live():
    # Test a real GDFlix link from active catalog using curl_cffi Chrome TLS impersonation
    gdflix_url = "https://new3.gdflix.io/file/ekmvapISgHELLR7"
    result = await resolve_gdflix_instant(gdflix_url)
    
    assert result["source_url"] == gdflix_url
    assert "filename" in result
    assert result.get("direct_url") is not None
    assert ("workers.dev" in result["direct_url"] or 
            "busycdn" in result["direct_url"] or 
            "fastcdn-dl" in result["direct_url"])
