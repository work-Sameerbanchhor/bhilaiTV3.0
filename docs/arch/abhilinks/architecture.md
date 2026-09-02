# Technical Architecture & Infrastructure Analysis: AbhiLinks

## 1. System Overview

AbhiLinks operates on a high-throughput, low-compute architecture designed specifically for rapid link delivery and high-volume referral traffic. The infrastructure isolates edge protection and caching from core database operations using a two-tier caching and reverse-proxy topology.

---

## 2. Infrastructure Layer Breakdown

### Layer 1: Edge Proxy, CDN & WAF (Cloudflare)
- **Role**: Perimeter defense, DDoS mitigation, TLS termination, bot management, and Anycast routing.
- **IP Infrastructure**: Cloudflare Anycast IP addresses `172.67.201.204` and `104.21.60.216`.
- **TLS Configuration**: TLS 1.3 / HTTP/2 and HTTP/3 support (`alt-svc: h3=":443"; ma=86400`). SSL certificate issued by **Google Trust Services LLC (WE1 CA)** covering `abhilinks.site` and `*.abhilinks.site`.
- **Edge Cache Status**:
  - HTML documents: `cf-cache-status: DYNAMIC` (requests are proxied directly to the origin LiteSpeed server without Cloudflare edge HTML caching).
  - Static assets (CSS/JS): Proxied through Cloudflare with standard edge asset caching.
- **WAF Directives**: Cloudflare managed challenge rules and Managed Content signals are present in `robots.txt`.

### Layer 2: Web Server & Micro-Caching (LiteSpeed Web Server)
- **Role**: High-concurrency web server handling LSAPI PHP processes and serving full-page cache directly from server memory/disk.
- **Identification**: Confirmed via headers `x-turbo-charged-by: LiteSpeed` and `server: cloudflare`.
- **LiteSpeed Cache (LSCache)**:
  - Cache Headers observed: `x-litespeed-cache: hit`, `x-litespeed-cache-control: public,max-age=604800`.
  - Cache Tagging: `x-litespeed-tag: 4b0_home,4b0_URL.<hash>,4b0_F,4b0_`
  - Single post pages (`/archives/<id>/`) are aggressively cached by LiteSpeed. Subsequent requests for the same post are served with zero PHP execution and zero database queries.
  - REST API requests (`/wp-json/wp/v2/*`) return `x-litespeed-cache-control: no-cache` and `cf-cache-status: DYNAMIC`, ensuring live data retrieval.

### Layer 3: Application Runtime (PHP & WordPress Engine)
- **CMS Platform**: WordPress (core version reported as `7.1` or modified WordPress 6.x fork).
- **PHP Execution Model**: LiteSpeed Server Application Programming Interface (LSPHP).
- **Core Configuration**:
  - Standard post type (`post`) handles all media entries.
  - No custom taxonomies or tag systems are configured.
  - Single default category ID `1` ("Uncategorized") contains all 15,451 items.
  - Permalinks are configured to custom numeric archive format `/archives/%post_id%/`.

### Layer 4: Custom Theme Layer (`m4u`)
- **Theme Identity**: `m4u` (Version 1.0.0, derived from Automattic's Underscores `_s` starter theme).
- **Asset Overhead**: Exceptionally minimal:
  - 1 CSS file: `https://abhilinks.site/wp-content/themes/m4u/style.css` (~1.8 KB).
  - 1 JS file: `https://abhilinks.site/wp-content/themes/m4u/js/navigation.js` (~2.9 KB).
  - External dependency: jQuery 3.7.0 (`cdnjs.cloudflare.com`).
- **Template Logic**:
  - Bypasses standard `the_content()` rendering.
  - Reads custom metadata fields (download links, resolution labels, episode IDs) and dynamically constructs styled container divs (`.download-links-div`, `.downloads-btns-div`).

### Layer 5: Data & Storage Tier
- **Database Engine**: MySQL / MariaDB (standard WordPress relational schema).
- **Data Distribution**:
  - `wp_posts`: Holds post ID, post title (containing movie name, year, audio, resolution descriptor), publication timestamp, modification timestamp, and slug.
  - `wp_postmeta`: Holds provider links (HubCloud and GDFlix URLs) mapped to specific resolutions or episode numbers.
- **Media Storage**: No local poster images or media attachments stored under `/wp-content/uploads/`. Zero thumbnail overhead.

### Layer 6: External File Lockers & Upstream Network
- **Referral / Inbound Traffic**: Upstream index `movieshunt.cc` and Telegram channels link directly to AbhiLinks archive pages.
- **Outbound Link Delivery**: Anchor buttons point directly to external file lockers:
  - `hubcloud.cx/drive/<hash>` (HUBCLOUD [DD] - Direct Download / Cloud drive)
  - `gdflix.dev/file/<hash>` (GDFlix - Google Drive proxy / cloud locker)

---

## 3. End-to-End Request Flow Diagram

```text
+-------------------------------------------------------------------------+
|                              VISITOR / CLIENT                            |
+-------------------------------------------------------------------------+
                                    |
                                    | HTTPS Request (GET /archives/42507/)
                                    v
+-------------------------------------------------------------------------+
|                          CLOUDFLARE EDGE (WAF/CDN)                      |
|  - DNS Resolution (Anycast 172.67.201.204 / 104.21.60.216)              |
|  - TLS 1.3 Handshake (GTS WE1 SSL Certificate)                          |
|  - WAF & Rate Limit Inspection                                          |
|  - Status: cf-cache-status: DYNAMIC (Proxies directly to origin)        |
+-------------------------------------------------------------------------+
                                    |
                                    | Origin Proxy Pass
                                    v
+-------------------------------------------------------------------------+
|                       LITESPEED WEB SERVER (LSWS)                       |
|  - Checks LSCache memory/disk hash for URL tag                          |
+-------------------------------------------------------------------------+
            |                                           |
    [ Cache Hit ]                               [ Cache Miss / API ]
            |                                           |
            v                                           v
+-----------------------+                   +-----------------------+
|  Serve Cached HTML    |                   |  PHP Worker (LSPHP)   |
|  x-litespeed-cache:   |                   |  - Executes WP Core   |
|  hit                  |                   |  - Queries Database   |
|  (Zero PHP Execution) |                   +-----------------------+
+-----------------------+                               |
            |                                           v
            |                               +-----------------------+
            |                               |   MySQL / MariaDB     |
            |                               |   - wp_posts          |
            |                               |   - wp_postmeta       |
            |                               +-----------------------+
            |                                           |
            +-------------------+-----------------------+
                                |
                                v
+-------------------------------------------------------------------------+
|                            RENDERED HTML OUTPUT                         |
|  - Header: Upstream Referral (movieshunt.cc)                            |
|  - Body: Resolution / Episode Button Grid                               |
|    * HubCloud: https://hubcloud.cx/drive/:hash                          |
|    * GDFlix:   https://gdflix.dev/file/:hash                            |
+-------------------------------------------------------------------------+
                                |
                                | User Clicks Outbound Link
                                v
+-------------------------------------------------------------------------+
|                       THIRD-PARTY FILE LOCKERS                          |
|  - hubcloud.cx                                                          |
|  - gdflix.dev                                                           |
+-------------------------------------------------------------------------+
```

---

## 4. Performance & Scalability Characteristics

1. **Micro-Caching Efficiency**: Because all single post pages are static HTML representations of metadata, LiteSpeed Cache serves them at raw web-server speed (typically < 15ms origin latency).
2. **Minimal Dynamic Load**: Dynamic PHP execution is triggered almost exclusively on search queries (`/?s=...`), REST API requests, or when new posts are published.
3. **Bandwidth Economy**: Without image assets, the entire HTML payload of a post is roughly 25 KB to 41 KB uncompressed, and ~6 KB gzipped.
