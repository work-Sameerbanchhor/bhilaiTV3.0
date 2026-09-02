import re
from typing import Dict, Any, List
from app.models import ParsedTitleInfo, LockerLink, ResolutionGroup, EpisodeGroup, ReleaseDetail

def parse_title(raw_title: str) -> ParsedTitleInfo:
    """
    Extracts clean metadata from standard release title strings.
    Examples:
      - 'Ozark Season 3 Dual Audio Hindi ORG. + English Netflix Original WEB Series WEB-DL 480p [220MB/E]'
      - 'Khamoshi: The Musical (1996) WEB-DL Hindi Full Movie'
      - 'Ali (2025) WEB-DL Bengali Full Movie'
    """
    title_str = raw_title.strip()
    
    # 1. Detect Year: (19xx|20xx) or bare 19xx|20xx
    year = None
    year_match = re.search(r'\(?(19\d\d|20\d\d)\)?', title_str)
    if year_match:
        year = year_match.group(1)

    # 2. Detect Season
    season = None
    season_match = re.search(r'\b(Season\s*\d+|S\d+)\b', title_str, re.IGNORECASE)
    if season_match:
        season = season_match.group(1).title()

    is_series = bool(season) or bool(re.search(r'\b(Series|Episodes?|Complete)\b', title_str, re.IGNORECASE))

    # 3. Detect Audio info
    audio = None
    audio_match = re.search(r'\b(Dual Audio|Multi Audio|Hindi Only|Hindi ORG|Hindi Dubbed|Hindi|English|Bengali|Tamil|Telugu|Korean|Japanese)\b', title_str, re.IGNORECASE)
    if audio_match:
        audio = audio_match.group(1).strip()

    # 4. Detect Quality
    quality = None
    qual_match = re.search(r'\b(480p|720p\s*HEVC|720p|1080p\s*HQ|1080p|2160p|4K|WEB-DL|HDRip|BluRay|HDTV)\b', title_str, re.IGNORECASE)
    if qual_match:
        quality = qual_match.group(1)

    # 5. Detect Size bracket [xxxMB] or [x.xGB]
    size = None
    size_match = re.search(r'\[([^\]]+)\]', title_str)
    if size_match:
        size = size_match.group(1).strip()

    # 6. Clean Title
    # Strip away brackets, Season, Year, Quality, and descriptors to get pure name
    clean = re.sub(r'\[[^\]]*\]', '', title_str)
    clean = re.sub(r'\((19\d\d|20\d\d)\)', '', clean)
    clean = re.sub(r'\b(Season\s*\d+|S\d+)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(Dual Audio|Multi Audio|Netflix Original|Amazon Original|Hotstar Special|Apple TV\+|WEB Series|Full Movie|Complete WEB Series|Complete|Dubbed|Filipino Drama|WEB-DL|HDRip|BluRay|480p|720p|1080p|HEVC|HQ|Hindi|English|Bengali|ORG\.?|With Subtitles)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'[\+\-\–\—\:\.\_]+', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    if not clean:
        clean = raw_title.split('(')[0].split('Season')[0].strip() or raw_title

    return ParsedTitleInfo(
        clean_title=clean,
        year=year,
        season=season,
        audio=audio,
        quality=quality,
        size=size,
        is_series=is_series
    )

def parse_post_html(post_id: int, raw_title: str, date: str, slug: str, post_url: str, html: str) -> ReleaseDetail:
    """
    Parses single post HTML into structured ReleaseDetail object
    with separate movie resolution tiers or series episode groupings.
    """
    parsed_info = parse_title(raw_title)
    
    # Extract upstream reference link if present
    upstream_match = re.search(r'<a[^>]+href=[\'"]([^\'"]*movieshunt\.cc[^\'"]*)[\'"]', html, re.IGNORECASE)
    upstream_url = upstream_match.group(1) if upstream_match else "https://movieshunt.cc/"

    # Check for series episodes (h5 containing -:Episodes: N:-)
    episode_sections = re.findall(r'<h5[^>]*>-(?:Episodes|Episode):\s*(\d+):-</h5>\s*<div class="downloads-btns-div">(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
    
    if not episode_sections:
        # Fallback regex for variations of episode headings
        episode_sections = re.findall(r'<h[45][^>]*>[^<]*Episode[s]?\s*[:\-]?\s*(\d+)[^<]*</h[45]>\s*<div[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)

    # Check for movie resolution groups (h4 containing 480p, 720p, etc.)
    resolution_sections = re.findall(r'<h4[^>]*>(.*?)</h4>\s*<div class="downloads-btns-div">(.*?)</div>', html, re.DOTALL | re.IGNORECASE)

    resolutions: List[ResolutionGroup] = []
    episodes: List[EpisodeGroup] = []

    def extract_links_from_chunk(chunk: str) -> List[LockerLink]:
        links: List[LockerLink] = []
        anchors = re.findall(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', chunk, re.DOTALL | re.IGNORECASE)
        for href, text in anchors:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            href = href.strip()
            
            if "hubcloud.cx" in href:
                links.append(LockerLink(
                    provider="HubCloud",
                    url=href,
                    label=clean_text or "HUBCLOUD [DD]",
                    is_primary=True,
                    badge="PRIMARY [DD]"
                ))
            elif "gdflix.dev" in href or "gdflix.io" in href:
                # Normalize domain to active working mirror https://new3.gdflix.io/
                file_hash = href.strip('/').split('/')[-1]
                normalized_url = f"https://new3.gdflix.io/file/{file_hash}"
                links.append(LockerLink(
                    provider="GDFlix",
                    url=normalized_url,
                    label="⚡ INSTANT DL (10GBPS)",
                    is_primary=False,
                    badge="10GBPS [GDFLIX]"
                ))
            elif "t.me" in href:
                links.append(LockerLink(
                    provider="Telegram",
                    url=href,
                    label="Telegram Stream",
                    is_primary=False,
                    badge="MIRROR [TG]"
                ))
        return links

    if episode_sections:
        release_type = "series"
        for ep_str, btn_chunk in episode_sections:
            try:
                ep_num = int(ep_str)
            except ValueError:
                ep_num = len(episodes) + 1
            ep_links = extract_links_from_chunk(btn_chunk)
            episodes.append(EpisodeGroup(
                episode_num=ep_num,
                title=f"Episode {ep_num}",
                links=ep_links
            ))
    elif resolution_sections:
        release_type = "movie"
        for qual_str, btn_chunk in resolution_sections:
            clean_qual = re.sub(r'<[^>]+>', '', qual_str).strip()
            
            # Extract size if in quality tag e.g. "1080p [2.4GB]"
            sz_match = re.search(r'\[([^\]]+)\]', clean_qual)
            size_val = sz_match.group(1) if sz_match else None
            
            res_links = extract_links_from_chunk(btn_chunk)
            resolutions.append(ResolutionGroup(
                quality=clean_qual,
                size=size_val,
                links=res_links
            ))
    else:
        # Fallback: extract all locker links from whole HTML
        release_type = "series" if parsed_info.is_series else "movie"
        all_links = extract_links_from_chunk(html)
        if all_links:
            resolutions.append(ResolutionGroup(
                quality=parsed_info.quality or "Default Quality",
                size=parsed_info.size,
                links=all_links
            ))

    return ReleaseDetail(
        id=post_id,
        raw_title=raw_title,
        parsed=parsed_info,
        date=date,
        slug=slug,
        url=post_url,
        release_type=release_type,
        resolutions=resolutions,
        episodes=episodes,
        upstream_url=upstream_url
    )
