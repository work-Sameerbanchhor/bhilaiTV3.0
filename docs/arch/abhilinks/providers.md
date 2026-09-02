# Download & Provider Ecosystem: AbhiLinks

## 1. Ecosystem Topology

AbhiLinks operates strictly as an intermediary landing bridge connecting upstream discovery portals with downstream file lockers. It does not host video files directly.

```text
+-------------------------------------------------------------+
|              UPSTREAM CANONICAL BILLBOARDS & ROTATIONS      |
|  - movieshunt.cc (Domain Billboard & Hub)                   |
|  - movies4u.review (Working Link Bookmark Directory)        |
|  - imovies4u.me (Automated Redirector to movies4u.review)   |
|  - t.me/Movieshunt_com (Telegram Channel)                   |
|  - tinyurl.com/xprime4u (Shortlink Referral)                |
+-------------------------------------------------------------+
                              |
                              | Links to specific release
                              v
+-------------------------------------------------------------+
|                   INTERMEDIARY GATEWAY (AbhiLinks)          |
|  https://abhilinks.site/archives/<id>/                      |
|  - Renders Resolution Options (480p, 720p, 1080p)           |
|  - Renders Episode Buttons (Episode 1, 2, ... N)            |
+-------------------------------------------------------------+
                              |
              +---------------+---------------+
              |                               |
              v                               v
+-----------------------------+ +-----------------------------+
|       HUBCLOUD LOCKER       | |        GDFLIX LOCKER        |
|  https://hubcloud.cx/       | |  https://gdflix.dev/        |
|  drive/:hash                | |  file/:hash                 |
+-----------------------------+ +-----------------------------+
              |                               |
              v                               v
+-------------------------------------------------------------+
|                   FINAL FILE DELIVERY                       |
|  - Direct CDN Download Stream                               |
|  - Cloud Drive Fast Download                                |
+-------------------------------------------------------------+
```

---

## 2. Downstream Provider Analysis

In our comprehensive sampling of posts across the catalog, 100% of download buttons route to two distinct file-locker domains:

### 1. HubCloud (`hubcloud.cx`)
- **Button Label**: `HUBCLOUD [DD]` (Direct Download)
- **URL Pattern**: `https://hubcloud.cx/drive/<alphanumeric_id>`
  - Example: `https://hubcloud.cx/drive/yx3i8todxvnv7j9`
- **Link Characteristics**:
  - Contains a unique 15-character alphanumeric token.
  - The token is static and persistent (stored directly in post metadata).
- **Public Behavior**:
  - Resolves with HTTP `200 OK` on standard GET requests.
  - Presents intermediate locker landing page offering Direct Download, Cloud Drive, and Telegram stream options.

### 2. GDFlix (`gdflix.dev` / `new3.gdflix.io`)
- **Button Label**: `GDFlix` / `SERVER 2`
- **Active Canonical Mirror**: `https://new3.gdflix.io/file/<alphanumeric_id>`
  - Example: `https://new3.gdflix.io/file/ekmvapISgHELLR7`
- **Link Characteristics**:
  - Contains a unique 15-character mixed-case alphanumeric token.
  - Normalized dynamically to `new3.gdflix.io` by BhilaiTV parser.
- **Public Behavior**:
  - Protected by Cloudflare Managed Challenge (`cf-mitigated: challenge`).
  - Headless Python requests (`httpx`/`urllib`) receive `HTTP 403 Forbidden`.
  - Bypassed headlessly in BhilaiTV using `curl_cffi` Chrome 120 TLS/JA3 impersonation to extract **FastCloud / ZipDisk (`cloud-dl.*.workers.dev`)** direct resumable media streams.

---

## 3. BhilaiTV Zero-Ad Direct Resolver Engine

To protect users from intrusive popunders, ad-trackers, malware scripts, and countdown timers, BhilaiTV implements a server-side zero-ad resolver engine:

```text
+-----------------------------------------------------------------------------------------+
|                                    BHILAITV FRONTEND                                    |
|   Modal Dialog: [ ⬇ SERVER 1 — DOWNLOAD ]         [ ⬇ SERVER 2 — DOWNLOAD ]             |
+-----------------------------------------------------------------------------------------+
                     │                                              │
                     │ GET /api/resolve/direct                      │ GET /api/resolve/gdflix
                     ▼                                              ▼
+------------------------------------------+   +------------------------------------------+
|          SERVER 1: HUBCLOUD R2           |   |       SERVER 2: GDFLIX FASTCLOUD         |
|  1. GET hubcloud.cx/drive/:hash          |   |  1. curl_cffi (Chrome 120 TLS Handshake) |
|  2. Extract HMAC token                   |   |  2. GET new3.gdflix.io/file/:hash        |
|  3. GET gamerxyt.com/hubcloud.php        |   |  3. POST /cflare/:id/:hash (action=cloud)|
|  4. Extract AWS SigV4 R2 presigned URL   |   |  4. Poll /cloud/...?token=...&xhr=1      |
|  -> *.r2.cloudflarestorage.com           |   |  -> cloud-dl.*.workers.dev (HTTP 206)    |
+------------------------------------------+   +------------------------------------------+
```

---

## 3. Post HTML Link Structure

Download links on AbhiLinks are structured into clean, deterministic HTML container hierarchies.

### Movie Release Structure (Grouped by Quality)
```html
<div class="download-links-div">
    <h4>480p [450MB]</h4>
    <div class="downloads-btns-div">
        <a href="https://hubcloud.cx/drive/kgkyg4uy7i3ii73" class="btn" target="_blank" style="background: linear-gradient(135deg,#e629d0,#007bff);color: white;"> HUBCLOUD [DD] </a>
        <a href="https://gdflix.dev/file/U8SZX8qRtle9olo" class="btn" target="_blank" style="background: linear-gradient(135deg, #007f33, #4d3438);color: white;"> GDFlix </a>
    </div>

    <h4>720p HEVC [700MB]</h4>
    <div class="downloads-btns-div">
        <a href="https://hubcloud.cx/drive/kv1qgev0ri34xex" class="btn" target="_blank" style="background: linear-gradient(135deg,#e629d0,#007bff);color: white;"> HUBCLOUD [DD] </a>
        <a href="https://gdflix.dev/file/s4xuuW4CZcrFIbI" class="btn" target="_blank" style="background: linear-gradient(135deg, #007f33, #4d3438);color: white;"> GDFlix </a>
    </div>

    <h4>1080p [2.4GB]</h4>
    <div class="downloads-btns-div">
        <a href="https://hubcloud.cx/drive/omaawhdmdpdb75b" class="btn" target="_blank" style="background: linear-gradient(135deg,#e629d0,#007bff);color: white;"> HUBCLOUD [DD] </a>
        <a href="https://gdflix.dev/file/GOTdUdlEtcaFpPw" class="btn" target="_blank" style="background: linear-gradient(135deg, #007f33, #4d3438);color: white;"> GDFlix </a>
    </div>
</div>
```

### Series Release Structure (Grouped by Episode)
```html
<div class="download-links-div">
    <h5>-:Episodes: 1:-</h5>
    <div class="downloads-btns-div">
        <a href="https://hubcloud.cx/drive/yx3i8todxvnv7j9" class="btn" target="_blank" style="background: linear-gradient(135deg,#e629d0,#007bff);color: white;"> HUBCLOUD [DD] </a>
        <a href="https://gdflix.dev/file/8fgJTUqlTWKJ874" class="btn" target="_blank" style="background: linear-gradient(135deg, #007f33, #4d3438);color: white;"> GDFlix </a>
    </div>

    <h5>-:Episodes: 2:-</h5>
    <div class="downloads-btns-div">
        <a href="https://hubcloud.cx/drive/9e4ruub4ea8ba4z" class="btn" target="_blank" style="background: linear-gradient(135deg,#e629d0,#007bff);color: white;"> HUBCLOUD [DD] </a>
        <a href="https://gdflix.dev/file/SVcY5D0O6zrUUZB" class="btn" target="_blank" style="background: linear-gradient(135deg, #007f33, #4d3438);color: white;"> GDFlix </a>
    </div>
</div>
```

---

## 4. Header & Footer Cross-Promotions

Every post page includes uniform upstream and community promotion links:
- **Upstream Official Website**: `https://movieshunt.cc/` (anchored in `<h1 class="entry-title">`)
- **Telegram Channel**: `https://t.me/Movieshunt_com`
- **Shortlink Portal**: `https://tinyurl.com/xprime4u`

---

## 5. Metadata Parser Extraction Grammar

Because the HTML structure is strictly regular, extracting metadata and locker links requires only simple deterministic regular expressions or CSS selectors:

| Extracted Field | Movie Extraction Pattern | Series Extraction Pattern |
| :--- | :--- | :--- |
| **Section Label** | `<h4>(.*?)</h4>` (e.g., `1080p [2.4GB]`) | `<h5>-:Episodes:\s*(\d+):-</h5>` (e.g., `Episode 1`) |
| **HubCloud Link** | `<a[^>]+href="([^"]+hubcloud\.cx/drive/[^"]+)"` | `<a[^>]+href="([^"]+hubcloud\.cx/drive/[^"]+)"` |
| **GDFlix Link** | `<a[^>]+href="([^"]+gdflix\.dev/file/[^"]+)"` | `<a[^>]+href="([^"]+gdflix\.dev/file/[^"]+)"` |
