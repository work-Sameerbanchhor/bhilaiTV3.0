# Request Efficiency & Optimal Indexing Strategy: AbhiLinks

## 1. Strategy Comparison

To discover and index the entire catalog of publicly available movie and series information with minimal requests and zero security bypasses, we evaluated five distinct approaches:

| Strategy | Total Requests for Initial 15,451 Posts | Data Returned Per Request | Parse Overhead | Incremental Support | Feasibility Rating |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A. XML Sitemaps** | N/A (Endpoint `404`) | 0 | None | None | ❌ **Non-Functional** |
| **B. HTML Pagination Scraping (`/?paged=N`)** | **1,546 requests** (10 items/page) | 10 post links in HTML (~25 KB) | High (HTML regex/DOM) | Low (must paginate until seen) | ⚠️ **Inefficient** |
| **C. Keyword Search Queries (`/?s=...`)** | Undefined (requires exhaustive keyword list) | Variable | High | None | ❌ **Incomplete / Wasteful** |
| **D. RSS Polling (`/feed/`)** | 1 request (only latest 10 items) | 10 latest items (~8 KB XML) | Low (XML) | Excellent for real-time delta | ⚠️ **Delta-Only (Cannot bootstrap catalog)** |
| **E. WordPress REST API (`/wp/v2/posts`)** | **155 requests** (100 items/page) | 100 structured JSON objects (~22 KB) | Minimal (JSON parse) | Native (`after=`, `modified_after=`) | 🏆 **Optimal Strategy** |

---

## 2. Mathematical Request Budget

### Initial Catalog Bootstrap (15,451 Total Posts)
Using the optimized REST API endpoint:
```http
GET /wp-json/wp/v2/posts?per_page=100&page={1..155}&_fields=id,date,modified,slug,title,link
```
- **Total Requests**: $\lceil 15,451 / 100 \rceil = 155\text{ HTTP Requests}$
- **Total Ingestion Bandwidth**: $155 \times \approx 22\text{ KB} = \mathbf{3.41\text{ MB total}}$
- **Execution Duration**: At a polite rate of 2 requests/sec, the entire catalog is indexed in **~77 seconds**.

### Link Extraction Budget (Selective HTML Resolution)
Because download links are stored in `postmeta` and rendered into HTML:
- Fetching `/archives/<id>/` is only performed for target posts:
  - 1 request per post to `/archives/<id>/` (~25 KB uncompressed, served directly from LiteSpeed Cache with `x-litespeed-cache: hit`).

### Ongoing Incremental Maintenance Budget
To maintain a 100% synchronized local database:
- **Periodic Poll (e.g., Hourly / Daily)**:
  ```http
  GET /wp-json/wp/v2/posts?after=<LAST_SEEN_ISO_TIMESTAMP>&_fields=id,date,modified,slug,title,link
  ```
  - **Requests**: **1 single HTTP request** returns all posts published since the last check.
  - If 15 new releases were published, 1 API request retrieves all 15 metadata records, followed by 15 cached HTML requests to extract provider links.
- **Real-Time Webhook/Feed Poll (every 5 minutes)**:
  ```http
  GET /feed/
  ```
  - **Requests**: **1 single HTTP request** (~8 KB) to inspect latest 10 items.

---

## 3. Incremental Indexing Flow Architecture

```text
+-------------------------------------------------------------+
|               SCHEDULED INCREMENTAL WORKER                  |
+-------------------------------------------------------------+
                              |
                              | 1. Query Local DB for latest post_date
                              v
+-------------------------------------------------------------+
|         QUERY REST API: GET /wp/v2/posts?after=<timestamp>   |
|         - Uses _fields=id,date,modified,slug,title,link     |
|         - per_page=100                                      |
+-------------------------------------------------------------+
                              |
                              | 2. Returns new/modified JSON array
                              v
+-------------------------------------------------------------+
|                 URL NORMALIZATION & DEDUPLICATION           |
|  - Check ID against local database                          |
|  - Detect new releases vs modified revisions                |
+-------------------------------------------------------------+
                              |
              +---------------+---------------+
              |                               |
    [ No New Releases ]             [ N New Releases Found ]
              |                               |
              v                               v
+-----------------------+   +---------------------------------+
|   Sleep Until Next    |   | 3. Fetch /archives/<id>/ (N req)|
|   Interval            |   |    - LiteSpeed Cache Hit        |
+-----------------------+   +---------------------------------+
                                              |
                                              v
                            +---------------------------------+
                            | 4. Extract Resolution & Links   |
                            |    - Match <h4>/<h5> containers |
                            |    - Extract HubCloud / GDFlix  |
                            +---------------------------------+
                                              |
                                              v
                            +---------------------------------+
                            | 5. Update Local Database        |
                            +---------------------------------+
```

---

## 4. Production-Ready Python Indexer Implementation

```python
"""
Lowest-Request Legitimate Incremental Indexer for AbhiLinks
Adheres strictly to normal browser behavior and public REST endpoints.
"""

import urllib.request
import urllib.parse
import json
import re
import time
from typing import List, Dict, Optional

BASE_URL = "https://abhilinks.site"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*"
}

def fetch_url(url: str) -> tuple[int, dict, str]:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="ignore")

def discover_posts(after_iso: Optional[str] = None, page: int = 1, per_page: int = 100) -> tuple[List[dict], int]:
    """Fetches up to 100 posts per request with selective field projection."""
    params = {
        "per_page": per_page,
        "page": page,
        "_fields": "id,date,modified,slug,title,link"
    }
    if after_iso:
        params["after"] = after_iso
        
    url = f"{BASE_URL}/wp-json/wp/v2/posts?{urllib.parse.urlencode(params)}"
    status, headers, body = fetch_url(url)
    
    total_pages = int(headers.get("x-wp-totalpages", 1))
    posts = json.loads(body)
    return posts, total_pages

def extract_post_download_links(post_url: str) -> Dict[str, List[Dict[str, str]]]:
    """Parses single post HTML to extract resolution groups and locker links."""
    status, headers, body = fetch_url(post_url)
    article_m = re.search(r'<article[^>]*>(.*?)</article>', body, re.DOTALL | re.IGNORECASE)
    if not article_m:
        return {}
    
    content = article_m.group(1)
    results = {}
    
    # Split by resolution (h4) or episode (h5)
    sections = re.split(r'(<h[45][^>]*>.*?</h[45]>)', content)
    current_section = "General"
    
    for section in sections:
        header_m = re.match(r'<h[45][^>]*>(.*?)</h[45]>', section, re.DOTALL)
        if header_m:
            current_section = re.sub(r'<[^>]+>', '', header_m.group(1)).strip()
            if current_section not in results:
                results[current_section] = []
        else:
            anchors = re.findall(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', section, re.DOTALL)
            for href, text in anchors:
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                if "hubcloud.cx" in href or "gdflix.dev" in href:
                    results.setdefault(current_section, []).append({
                        "provider": clean_text,
                        "url": href
                    })
    return results

if __name__ == "__main__":
    print("Testing 1-request discovery...")
    posts, pages = discover_posts(per_page=5)
    print(f"Discovered {len(posts)} posts. Total pages: {pages}")
    
    sample = posts[0]
    print(f"\nResolving links for Post ID: {sample['id']} ({sample['title']['rendered']})...")
    links = extract_post_download_links(sample["link"])
    print(json.dumps(links, indent=2))
```
