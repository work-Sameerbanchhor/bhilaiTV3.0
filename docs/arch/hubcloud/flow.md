# HubCloud Link Resolution & Execution Flow

## 1. Step-by-Step Resolution Flow

```text
Step 1: Inbound Request from Landing Gateway
GET https://hubcloud.cx/drive/yx3i8todxvnv7j9
Headers: Referer: https://abhilinks.site/archives/42507/
   │
   ▼
Step 2: HubCloud Edge Response (Cloudflare Cache HIT)
Status: HTTP/2 200 OK
Payload: HTML document containing metadata + inline JS token
   │
   ▼
Step 3: Client Script Execution & Token Extraction
JS extracts variable `url`:
https://gamerxyt.com/hubcloud.php?host=hubcloud&id=yx3i8todxvnv7j9&token=MS9nUjVX...
Sets cookie `xlax=s4t; expires=...; SameSite=None; Secure`
Loads ad popunder scripts: //d33f51dyacx7bd.cloudfront.net/?aydfd=1015073
   │
   ▼
Step 4: User Action / Automatic Navigation (2000ms delay)
GET https://gamerxyt.com/hubcloud.php?host=hubcloud&id=yx3i8todxvnv7j9&token=...
   │
   ▼
Step 5: Final Delivery Selection
Intermediate gateway verifies token validity and presents final download endpoints:
1. Fast Direct Download Stream (CDN mirror)
2. Cloud Storage Direct Link (Google Drive / FSLocker)
3. Telegram Stream Bot Link
```

---

## 2. Extraction Recipe for Legitimate Metadata Discovery

For an indexer seeking only publicly disclosed technical file attributes (filename, exact size, container type) without executing advertisements or completing redirects:

```python
import urllib.request
import re

def extract_hubcloud_metadata(drive_url: str) -> dict:
    req = urllib.request.Request(drive_url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://abhilinks.site/"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        
    title_m = re.search(r'<title>(.*?)</title>', html)
    filename = title_m.group(1).strip() if title_m else ""
    
    size_m = re.search(r'File Size:\s*<strong>(.*?)</strong>', html)
    file_size = size_m.group(1).strip() if size_m else ""
    
    type_m = re.search(r'File Type:\s*<strong>(.*?)</strong>', html)
    mime_type = type_m.group(1).strip() if type_m else ""
    
    date_m = re.search(r'Share Date:\s*<strong>(.*?)</strong>', html)
    share_date = date_m.group(1).strip() if date_m else ""
    
    return {
        "filename": filename,
        "file_size": file_size,
        "mime_type": mime_type,
        "share_date": share_date,
        "hubcloud_url": drive_url
    }
```
