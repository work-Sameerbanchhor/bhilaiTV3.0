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
    
    # Verify GDFlix domain normalization to new3.gdflix.io
    gd_link = [l for l in detail.resolutions[0].links if l.provider == "GDFlix"][0]
    assert gd_link.url == "https://new3.gdflix.io/file/U8SZX8qRtle9olo"

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
            <a href="https://new3.gdflix.io/file/SVcY5D0O6zrUUZB" class="btn"> GDFlix </a>
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
    
    # Check normalized GDFlix URL on episode 1
    gd_link = [l for l in detail.episodes[0].links if l.provider == "GDFlix"][0]
    assert gd_link.url == "https://new3.gdflix.io/file/8fgJTUqlTWKJ874"
