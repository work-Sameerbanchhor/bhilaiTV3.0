import pytest
from app.services.parser import parse_title, parse_post_html

def test_movie_title_parsing():
    raw_title = "Download Fighter (2024) Hindi Movie 480p | 720p | 1080p WEB-DL"
    parsed = parse_title(raw_title)
    
    assert parsed.year == "2024"
    assert parsed.is_series is False
    assert "Fighter" in parsed.clean_title
    assert parsed.audio is not None
    assert "Hindi" in parsed.audio

def test_series_title_parsing():
    raw_title = "Download Ozark Season 4 Complete Hindi Dubbed Dual Audio 720p 1080p WEB-DL"
    parsed = parse_title(raw_title)
    
    assert parsed.is_series is True
    assert "Season 4" in parsed.season
    assert "Ozark" in parsed.clean_title

def test_reacher_long_series_title_parsing():
    raw_title = "Reacher Season 3 Multi Audio Hindi ORG. + English + Tamil + Telugu + Malayalam + Kannada Complete Amazon Prime WEB Series WEB-DL 720p [650MB/E]"
    parsed = parse_title(raw_title)
    
    assert parsed.clean_title == "Reacher"
    assert parsed.season == "Season 3"
    assert parsed.quality == "720P"
    assert parsed.size == "650MB/E"
    assert parsed.audio == "Multi Audio"
    assert parsed.is_series is True

def test_movie_post_html_parsing():
    html_content = """
    <div class="download-links-div">
        <h4>480p [450MB]</h4>
        <div class="downloads-btns-div">
            <a href="https://hubcloud.cx/drive/kgkyg4uy7i3ii73" class="btn"> HUBCLOUD [DD] </a>
            <a href="https://gdflix.dev/file/U8SZX8qRtle9olo" class="btn"> GDFlix </a>
        </div>
        <h4>1080p [2.4GB]</h4>
        <div class="downloads-btns-div">
            <a href="https://hubcloud.cx/drive/omaawhdmdpdb75b" class="btn"> HUBCLOUD [DD] </a>
            <a href="https://new3.gdflix.io/file/GOTdUdlEtcaFpPw" class="btn"> GDFlix </a>
        </div>
    </div>
    """
    detail = parse_post_html(
        post_id=101,
        raw_title="Fighter (2024) Hindi Movie 480p 1080p",
        date="2024-01-01",
        slug="fighter-2024",
        post_url="https://abhilinks.site/archives/101",
        html=html_content
    )
    
    assert detail.release_type == "movie"
    assert len(detail.resolutions) == 2
    assert "480p" in detail.resolutions[0].quality
    assert len(detail.resolutions[0].links) == 2
    
    # Verify HubCloud provider
    hub_link = [l for l in detail.resolutions[0].links if l.provider == "HubCloud"][0]
    assert "hubcloud.cx/drive/" in hub_link.url
    
    # Verify GDFlix domain and file ID
    gd_link = [l for l in detail.resolutions[0].links if l.provider == "GDFlix"][0]
    assert "file/U8SZX8qRtle9olo" in gd_link.url
    assert "gdflix" in gd_link.url

def test_series_post_html_parsing():
    html_content = """
    <div class="download-links-div">
        <h5>-:Episodes: 1:-</h5>
        <div class="downloads-btns-div">
            <a href="https://hubcloud.cx/drive/yx3i8todxvnv7j9" class="btn"> HUBCLOUD [DD] </a>
            <a href="https://gdflix.dev/file/8fgJTUqlTWKJ874" class="btn"> GDFlix </a>
        </div>
        <h5>-:Episodes: 2:-</h5>
        <div class="downloads-btns-div">
            <a href="https://hubcloud.cx/drive/9e4ruub4ea8ba4z" class="btn"> HUBCLOUD [DD] </a>
            <a href="https://new4.gdflix.io/file/SVcY5D0O6zrUUZB" class="btn"> GDFlix </a>
        </div>
    </div>
    """
    detail = parse_post_html(
        post_id=202,
        raw_title="Ozark Season 1 Complete",
        date="2024-01-01",
        slug="ozark-s01",
        post_url="https://abhilinks.site/archives/202",
        html=html_content
    )
    
    assert detail.release_type == "series"
    assert len(detail.episodes) == 2
    assert detail.episodes[0].episode_num == 1
    assert detail.episodes[1].episode_num == 2
    assert len(detail.episodes[0].links) == 2
    
    # Check GDFlix URL on episode 1
    gd_link = [l for l in detail.episodes[0].links if l.provider == "GDFlix"][0]
    assert "file/8fgJTUqlTWKJ874" in gd_link.url
    assert "gdflix" in gd_link.url

def test_series_zip_pack_html_parsing():
    html_content = """
    <div class="download-links-div">
        <h4>720p [4.6GB]</h4>
        <div class="downloads-btns-div">
            <a href="https://hubcloud.cx/drive/zip720p" class="btn"> HUBCLOUD [DD] </a>
        </div>
        <h4>1080p [8.1GB]</h4>
        <div class="downloads-btns-div">
            <a href="https://hubcloud.cx/drive/zip1080p" class="btn"> HUBCLOUD [DD] </a>
        </div>
    </div>
    """
    detail = parse_post_html(
        post_id=303,
        raw_title="The Purge Season 2 Dual Audio Hindi ORG. Complete Amazon Prime WEB Series BluRay",
        date="2024-01-01",
        slug="the-purge-s02",
        post_url="https://abhilinks.site/archives/303",
        html=html_content
    )
    
    assert detail.release_type == "series"
    assert detail.parsed.is_series is True
    assert detail.parsed.season == "Season 2"
    assert len(detail.resolutions) == 2
    assert "720p" in detail.resolutions[0].quality
    assert detail.resolutions[0].size == "4.6GB"

def test_new_link_patterns_and_domain_auto_discovery():
    from app.services.domain_registry import domain_registry
    
    html_content = """
    <div class="download-links-div">
        <h4>1080p [2.1GB]</h4>
        <div class="downloads-btns-div">
            <a href="https://hubcloud.ist/drive/ydy1xcejef1j11c" class="btn"> HUBCLOUD [DD] </a>
            <a href="https://new4.gdflix.io/file/GxqYhvIs1pGH6cE" class="btn"> GDFlix </a>
        </div>
    </div>
    """
    detail = parse_post_html(
        post_id=404,
        raw_title="Seek (2025) WEB-DL Dual Audio Hindi ORG + Japanese Full Movie",
        date="2025-01-01",
        slug="seek-2025",
        post_url="https://abhilinks.site/archives/404",
        html=html_content
    )
    
    assert len(detail.resolutions) == 1
    links = detail.resolutions[0].links
    assert len(links) == 2
    
    hub = [l for l in links if l.provider == "HubCloud"][0]
    assert "hubcloud.ist/drive/ydy1xcejef1j11c" in hub.url
    
    gdf = [l for l in links if l.provider == "GDFlix"][0]
    assert "new4.gdflix.io/file/GxqYhvIs1pGH6cE" in gdf.url
    
    # Verify domain registry learned the active domains
    assert "hubcloud.ist" in domain_registry._hubcloud_domains
    assert "new4.gdflix.io" in domain_registry._gdflix_domains


