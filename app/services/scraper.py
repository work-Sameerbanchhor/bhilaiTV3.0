import httpx
import time
import asyncio
import re
from typing import Optional, Dict, Any
from app.config import REST_API_URL, BASE_URL, DEFAULT_HEADERS, HTTP_TIMEOUT
from app.models import ReleaseItem, SearchResponse, ReleaseDetail, SeriesQualitySibling
from app.services.parser import parse_title, parse_post_html

# Maximum entries per in-memory cache to prevent unbounded growth in production
MAX_CACHE_ENTRIES = 1000

def _prune_cache_if_needed(cache_dict: dict, max_entries: int = MAX_CACHE_ENTRIES):
    """Evicts the oldest 20% of entries when cache exceeds capacity."""
    if len(cache_dict) > max_entries:
        evict_count = int(max_entries * 0.2)
        for k in list(cache_dict.keys())[:evict_count]:
            cache_dict.pop(k, None)

# In-memory detail cache: {post_id: (timestamp, ReleaseDetail)}
_DETAIL_CACHE: Dict[int, tuple[float, ReleaseDetail]] = {}
CACHE_TTL = 600  # 10 minutes

# In-memory poster cache: {clean_title: poster_url}
_POSTER_CACHE: Dict[str, Optional[str]] = {}

# Persistent HTTP Clients with Connection Pooling per event loop
_CLIENTS_BY_LOOP: Dict[asyncio.AbstractEventLoop, httpx.AsyncClient] = {}

async def get_http_client() -> httpx.AsyncClient:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    client = _CLIENTS_BY_LOOP.get(loop)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=HTTP_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=25, max_connections=60),
            follow_redirects=True
        )
        if loop is not None:
            _CLIENTS_BY_LOOP[loop] = client
    return client

async def get_movie_poster(clean_title: str) -> Optional[str]:
    """
    Asynchronously retrieves the official TMDB movie/series poster from MoviesHunt.
    Caches results in memory for instantaneous sub-millisecond retrieval.
    """
    if not clean_title:
        return None
    
    clean = clean_title.strip()
    if clean in _POSTER_CACHE:
        return _POSTER_CACHE[clean]
    
    _prune_cache_if_needed(_POSTER_CACHE)
    
    try:
        client = await get_http_client()
        search_url = f"https://movieshunt.casa/?s={clean}"
        r = await client.get(search_url, timeout=5.0)
        if r.status_code == 200:
            art_match = re.search(r'<article[^>]*>.*?<img[^>]+src=[\"\x27]([^\"]+)[\"\x27]', r.text, re.DOTALL | re.I)
            if art_match:
                url = art_match.group(1).strip()
                # Optimize TMDB image size: replace /original/ with /w342/ for compact fast loading
                if "image.tmdb.org/t/p/" in url:
                    url = re.sub(r'/t/p/(?:original|w\d+)/', '/t/p/w342/', url)
                _POSTER_CACHE[clean] = url
                return url
    except Exception:
        pass
        
    _POSTER_CACHE[clean] = None
    return None

async def fetch_latest_releases(page: int = 1, per_page: int = 20) -> SearchResponse:
    """
    Fetches the latest published releases from AbhiLinks REST API.
    """
    params = {
        "page": page,
        "per_page": min(per_page, 50),
        "_fields": "id,date,modified,slug,title,link"
    }
    url = f"{REST_API_URL}/posts"
    
    client = await get_http_client()
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

    # Concurrently attach movie/series posters
    clean_titles = [it.parsed.clean_title for it in items]
    posters = await asyncio.gather(*[get_movie_poster(t) for t in clean_titles], return_exceptions=True)
    for it, p in zip(items, posters):
        if isinstance(p, str):
            it.poster_url = p
        
    return SearchResponse(
        results=items,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        query=None
    )

async def search_releases(query: str, page: int = 1, per_page: int = 20) -> SearchResponse:
    """
    Executes a search query against the AbhiLinks REST API.
    """
    params = {
        "search": query.strip(),
        "page": page,
        "per_page": min(per_page, 50),
        "_fields": "id,date,modified,slug,title,link"
    }
    url = f"{REST_API_URL}/posts"
    
    client = await get_http_client()
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

    # Concurrently attach movie/series posters
    clean_titles = [it.parsed.clean_title for it in items]
    posters = await asyncio.gather(*[get_movie_poster(t) for t in clean_titles], return_exceptions=True)
    for it, p in zip(items, posters):
        if isinstance(p, str):
            it.poster_url = p
        
    return SearchResponse(
        results=items,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        query=query
    )

async def fetch_release_detail(post_id: int) -> ReleaseDetail:
    """
    Fetches the single post page, parses download buttons and resolutions.
    Employs an in-memory micro-cache.
    """
    if post_id <= 0:
        raise ValueError(f"Invalid post ID: {post_id}")

    now = time.time()
    if post_id in _DETAIL_CACHE:
        cached_time, cached_detail = _DETAIL_CACHE[post_id]
        if now - cached_time < CACHE_TTL:
            return cached_detail

    # 1. Fetch metadata from REST API to get exact raw title
    client = await get_http_client()
    post_api_url = f"{REST_API_URL}/posts/{post_id}?_fields=id,date,slug,title,link"
    post_resp = await client.get(post_api_url)
    
    if post_resp.status_code == 200:
        post_data = post_resp.json()
        raw_title = post_data.get("title", {}).get("rendered", "")
        date_str = post_data.get("date", "")
        slug_str = post_data.get("slug", "")
        post_url = post_data.get("link", f"{BASE_URL}/archives/{post_id}/")
    elif post_resp.status_code == 404:
        raise ValueError(f"Release #{post_id} does not exist on upstream provider")
    else:
        raw_title = f"Release #{post_id}"
        date_str = ""
        slug_str = ""
        post_url = f"{BASE_URL}/archives/{post_id}/"

    # 2. Fetch rendered HTML
    html_resp = await client.get(post_url)
    html_resp.raise_for_status()
    html = html_resp.text

    detail = parse_post_html(
        post_id=post_id,
        raw_title=raw_title,
        date=date_str,
        slug=slug_str,
        post_url=post_url,
        html=html
    )
    
    # 3. If series, query sibling resolution posts for the same show and season
    if detail.release_type == "series" and detail.parsed.clean_title:
        try:
            search_term = f"{detail.parsed.clean_title}"
            if detail.parsed.season:
                search_term += f" {detail.parsed.season}"
            
            sibling_resp = await client.get(
                f"{REST_API_URL}/posts",
                params={"search": search_term, "per_page": 12, "_fields": "id,title"}
            )
            if sibling_resp.status_code == 200:
                sibling_posts = sibling_resp.json()
                siblings_map = {}
                for sp in sibling_posts:
                    sp_id = sp.get("id")
                    sp_title = sp.get("title", {}).get("rendered", "")
                    sp_info = parse_title(sp_title)
                    
                    is_title_match = sp_info.clean_title.lower() == detail.parsed.clean_title.lower()
                    is_season_match = (sp_info.season == detail.parsed.season) if detail.parsed.season else True
                    
                    if is_title_match and is_season_match and sp_info.quality:
                        siblings_map[sp_id] = SeriesQualitySibling(
                            post_id=sp_id,
                            quality=sp_info.quality,
                            size=sp_info.size,
                            is_current=(sp_id == post_id)
                        )
                
                if post_id not in siblings_map and detail.parsed.quality:
                    siblings_map[post_id] = SeriesQualitySibling(
                        post_id=post_id,
                        quality=detail.parsed.quality,
                        size=detail.parsed.size,
                        is_current=True
                    )
                
                def quality_sort_key(s: SeriesQualitySibling):
                    q = s.quality.upper()
                    if "480" in q: return 1
                    if "720" in q and "HEVC" not in q: return 2
                    if "720" in q and "HEVC" in q: return 3
                    if "1080" in q and "HQ" not in q: return 4
                    if "1080" in q and "HQ" in q: return 5
                    if "2160" in q or "4K" in q: return 6
                    return 99
                
                # If specific resolutions exist, remove generic non-sized siblings
                has_specific_res = any(any(r in s.quality.upper() for r in ["480", "720", "1080", "2160", "4K"]) for s in siblings_map.values())
                filtered_siblings = [
                    s for s in siblings_map.values()
                    if not (has_specific_res and s.quality.upper() in ["WEB-DL", "BLURAY", "HDRIP", "HDTV"] and not s.size)
                ]
                detail.sibling_qualities = sorted(filtered_siblings, key=quality_sort_key)
        except Exception:
            pass

    # 4. Fetch movie/series poster
    if detail.parsed.clean_title:
        try:
            detail.poster_url = await get_movie_poster(detail.parsed.clean_title)
        except Exception:
            pass

    _prune_cache_if_needed(_DETAIL_CACHE)
    _DETAIL_CACHE[post_id] = (now, detail)
    return detail

_RESOLVE_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}
RESOLVE_TTL = 18000  # 5 hours (direct R2 presigned links last 8 hours)

async def resolve_hubcloud_direct_links(hubcloud_url: str) -> Dict[str, Any]:
    """
    Server-side resolver that navigates through HubCloud and its intermediate handoff,
    extracting clean, ZERO-AD direct Cloudflare R2 presigned links, 10Gbps CDN streams,
    Pixeldrain mirrors, and Telegram streams.
    """
    now = time.time()
    if hubcloud_url in _RESOLVE_CACHE:
        cached_time, cached_res = _RESOLVE_CACHE[hubcloud_url]
        if now - cached_time < RESOLVE_TTL:
            return cached_res

    import re
    headers = dict(DEFAULT_HEADERS)
    headers["Referer"] = "https://hubcloud.cx/"

    async with httpx.AsyncClient(headers=headers, timeout=12.0, verify=False, follow_redirects=True) as client:
        # 1. Fetch HubCloud page
        r1 = await client.get(hubcloud_url)
        html1 = r1.text

        token_m = re.search(r"var url = ['\"](https://gamerxyt\.com/hubcloud\.php\?[^'\"]+)['\"];", html1)
        if not token_m:
            raise ValueError("Token not found in HubCloud page or link invalid")

        next_url = token_m.group(1)

        # 2. Fetch gamerxyt.com intermediate page
        r2 = await client.get(next_url)
        html2 = r2.text

        # 3. Extract direct links from anchors
        anchors = re.findall(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html2, re.DOTALL | re.IGNORECASE)

        direct_links = []
        for href, text in anchors:
            clean_t = re.sub(r'<[^>]+>', '', text).strip()
            if "r2.cloudflarestorage.com" in href:
                direct_links.append({
                    "type": "r2_direct",
                    "provider": "Cloudflare R2",
                    "label": "Direct Fast Download (Cloudflare R2)",
                    "badge": "⚡ ZERO_ADS [R2]",
                    "url": href,
                    "is_direct": True
                })
            elif "gpdl.hubcloud.cx" in href:
                direct_links.append({
                    "type": "gpdl_cdn",
                    "provider": "10Gbps CDN",
                    "label": "10Gbps High-Speed Stream",
                    "badge": "⚡ CDN_10GBPS",
                    "url": href,
                    "is_direct": True
                })
            elif "pixeldrain.dev" in href or "pixeldrain.com" in href:
                direct_links.append({
                    "type": "pixeldrain",
                    "provider": "PixelDrain",
                    "label": "PixelDrain Fast Mirror",
                    "badge": "📦 MIRROR",
                    "url": href,
                    "is_direct": False
                })
            elif "fuckingfast.net" in href:
                direct_links.append({
                    "type": "buzz_server",
                    "provider": "Buzz Server",
                    "label": "Buzz Fast Server",
                    "badge": "⚡ FAST_MIRROR",
                    "url": href,
                    "is_direct": False
                })
            elif "hubcloud.cx/tg/go" in href:
                direct_links.append({
                    "type": "telegram",
                    "provider": "Telegram",
                    "label": "Telegram Direct Stream",
                    "badge": "✈️ TELEGRAM",
                    "url": href,
                    "is_direct": True
                })

        result = {
            "source_url": hubcloud_url,
            "direct_links": direct_links,
            "total_links": len(direct_links)
        }

        _prune_cache_if_needed(_RESOLVE_CACHE)
        _RESOLVE_CACHE[hubcloud_url] = (now, result)
        return result

async def close_http_client():
    """Gracefully closes persistent HTTP clients on application shutdown."""
    global _CLIENTS_BY_LOOP
    for loop, client in list(_CLIENTS_BY_LOOP.items()):
        if client is not None and not client.is_closed:
            await client.aclose()
    _CLIENTS_BY_LOOP.clear()
