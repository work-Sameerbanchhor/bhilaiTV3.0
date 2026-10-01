import re
import time
import asyncio
from typing import Dict, Any, Optional
from curl_cffi.requests import Session
from app.services.domain_registry import domain_registry

_GDFLIX_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}
GDFLIX_CACHE_TTL = 3600  # 1 hour

def _resolve_fastcloud_stream(session: Session, base_url: str, cflare_href: str) -> Optional[str]:
    """
    Resolves FAST CLOUD / ZIPDISK link to direct Cloudflare Worker stream:
    1. GET /cflare/... to extract session key
    2. POST /cflare/... to generate cloud task
    3. Poll /cloud/... with ?xhr=1 to get task redirect (with queue retry)
    4. GET final /cloud/... page to extract direct cloud-dl.*.workers.dev download link
    """
    try:
        cflare_url = base_url + cflare_href if not cflare_href.startswith("http") else cflare_href
        r_cflare = session.get(cflare_url, timeout=6)
        if r_cflare.status_code != 200:
            return None

        key_m = re.search(r'formData\.append\("key",\s*"([^"]+)"\)', r_cflare.text)
        key = key_m.group(1) if key_m else ""

        # Step 2: POST to request cloud generation
        post_data = {"action": "cloud", "key": key, "action_token": ""}
        headers = {
            "x-token": base_url.replace("https://", "").replace("http://", "").split("/")[0],
            "Referer": cflare_url,
            "Origin": base_url
        }
        r_post = session.post(cflare_url, data=post_data, headers=headers, timeout=6)
        if r_post.status_code != 200:
            return None

        p_json = r_post.json()
        cloud_path = p_json.get("url")
        if not cloud_path:
            return None

        cloud_url = base_url + cloud_path if not cloud_path.startswith("http") else cloud_path

        # Step 3: Poll for completion redirect (handles QUEUED tasks)
        poll_url = cloud_url + ("&xhr=1" if "?" in cloud_url else "?xhr=1")
        poll_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": cloud_url
        }
        
        redirect_path = None
        for _ in range(4):
            r_poll = session.get(poll_url, headers=poll_headers, timeout=5)
            if r_poll.status_code == 200:
                try:
                    poll_json = r_poll.json()
                    redirect_path = poll_json.get("redirect")
                    if redirect_path:
                        break
                    if poll_json.get("status") == "QUEUED":
                        time.sleep(1)
                except Exception:
                    break
            else:
                break

        if not redirect_path:
            return None

        final_cloud_url = base_url + redirect_path if not redirect_path.startswith("http") else redirect_path

        # Step 4: Extract direct worker stream link
        r_final = session.get(final_cloud_url, timeout=6)
        if r_final.status_code != 200:
            return None

        # Look for Cloud Resume Download / workers.dev / direct link
        worker_m = re.search(r'href=[\'"](https?://[^\'"]*(?:workers\.dev|fastcdn-dl|r2\.dev|busycdn|foxcloud)[^\'"]+)[\'"]', r_final.text)
        if worker_m:
            return worker_m.group(1)

        # Fallback: any direct anchor that is not navigation/login
        anchors = re.findall(r'<a\s+[^>]*href=[\'"](https?://[^\'"]+)[\'"][^>]*>(.*?)</a>', r_final.text, re.DOTALL | re.IGNORECASE)
        for href, text in anchors:
            if not any(skip in href for skip in ['gdflix.io', 'telegram', 't.me', 'login', 'about', 'policy', 'contact']):
                return href

        return None
    except Exception:
        return None

def _fetch_gdflix_sync(gdflix_url: str) -> Dict[str, Any]:
    """
    Synchronous curl_cffi fetch — Chrome TLS impersonation bypasses Cloudflare Turnstile.
    Dynamically iterates candidate mirrors (e.g. gdflix.dev, new4.gdflix.io) and auto-fails over
    if an old or dead mirror is passed.
    """
    candidate_urls = domain_registry.get_gdflix_candidate_urls(gdflix_url)
    last_err = None

    for candidate in candidate_urls:
        try:
            with Session(impersonate="chrome120") as session:
                r = session.get(candidate, timeout=4.5, allow_redirects=True)

                if r.status_code != 200:
                    domain_registry.mark_domain_failed(candidate)
                    continue

                html = r.text
                landed_url = str(r.url)
                base_url = "https://" + landed_url.replace("https://", "").replace("http://", "").split("/")[0]

                anchors = re.findall(
                    r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>',
                    html, re.DOTALL | re.IGNORECASE
                )

                found: Dict[str, str] = {}
                cflare_href = None

                for href, text in anchors:
                    href = href.strip()
                    if "cflare" in href:
                        cflare_href = href

                    if not href.startswith("http"):
                        continue

                    if any(k in href for k in ["instant.busycdn", "instant.gdflix", "foxcloud", "quick.", "busycdn"]):
                        found["instant_10gbps"] = href
                    elif any(k in href for k in ["fastcdn-dl", "r2.dev", "r2.cloudflarestorage"]):
                        found["cloud_r2"] = href
                    elif "workers.dev" in href:
                        found["workers_mirror"] = href
                    elif "drivebot" in href:
                        found["drivebot"] = href
                    elif "indexserver" in href:
                        found["direct_server"] = href

                # Extract FastCloud / ZipDisk stream if cflare path is present
                fastcloud_url = None
                if cflare_href:
                    fastcloud_url = _resolve_fastcloud_stream(session, base_url, cflare_href)

                # Primary download target: prefer FastCloud, then Instant DL, then R2, then worker mirror/drivebot
                primary_download = (
                    fastcloud_url or
                    found.get("instant_10gbps") or
                    found.get("cloud_r2") or
                    found.get("workers_mirror") or
                    found.get("drivebot") or
                    found.get("direct_server")
                )

                title_m = re.search(r'<title>GDFlix \| (.*?)</title>', html, re.IGNORECASE)
                filename = title_m.group(1).strip() if title_m else "Unknown File"

                if primary_download or found:
                    domain_registry.mark_gdflix_success(base_url)
                    return {
                        "source_url": gdflix_url,
                        "filename": filename,
                        "fastcloud_zipdisk": fastcloud_url,
                        "instant_10gbps": found.get("instant_10gbps"),
                        "cloud_r2": found.get("cloud_r2"),
                        "direct_url": primary_download,
                        "resolved_domain": base_url,
                        "all_links": found
                    }

        except Exception as e:
            last_err = e
            domain_registry.mark_domain_failed(candidate)
            continue

    raise ValueError(f"No direct download stream found on this GDFlix page across candidate mirrors: {last_err}")

async def resolve_gdflix_instant(gdflix_url: str) -> Dict[str, Any]:
    """
    Async wrapper — runs the sync curl_cffi session in a thread executor
    to avoid event loop conflicts with uvicorn.
    """
    now = time.time()
    if gdflix_url in _GDFLIX_CACHE:
        cached_time, cached = _GDFLIX_CACHE[gdflix_url]
        if now - cached_time < GDFLIX_CACHE_TTL:
            return cached

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _fetch_gdflix_sync, gdflix_url)

    _GDFLIX_CACHE[gdflix_url] = (now, result)
    return result
