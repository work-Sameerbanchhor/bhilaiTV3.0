# HubCloud Architecture & System Design

## 1. Network & Edge Infrastructure

HubCloud is architected to handle massive referral spikes while protecting backend storage nodes from direct public scanning and origin exhaustion.

### Edge Tier (Cloudflare Anycast)
- **Host**: `hubcloud.cx`
- **Anycast IPs**: `172.67.199.249`, `104.21.44.126` (Cloudflare AS13335)
- **SSL / TLS**: TLS 1.3 / HTTP/2 & HTTP/3 via Google Trust Services WE1 CA.
- **Edge Caching Behavior**:
  - Unlike AbhiLinks (which sets `cf-cache-status: DYNAMIC`), HubCloud drive pages return **`cf-cache-status: HIT`**.
  - Drive landing pages are aggressively micro-cached across Cloudflare's global edge points of presence (PoPs).
  - This allows HubCloud to absorb massive concurrent click-throughs from movie landing sites with near-zero origin server load.

---

## 2. Page Structure & Metadata Exposure

When a client requests `https://hubcloud.cx/drive/<hash>`, HubCloud responds with an HTML page built on Bootstrap 5 and FontAwesome.

### HTML Elements & Extracted Schema

```html
<!-- Title exposes the full source filename -->
<title>(Movies4u.Foo).Ozark.S03E01.480p.WEB-DL.Hindi.English.ESub.x264.mkv</title>

<!-- File Details List -->
<ul class="list-unstyled">
    <li><i class="fas fa-file-video"></i> File Size: <strong>234.84 MB</strong></li>
    <li><i class="fas fa-file-alt"></i> File Type: <strong>video/matroska</strong></li>
    <li><i class="fas fa-calendar-alt"></i> Share Date: <strong>31-Aug-2026 07:08:11</strong></li>
</ul>
```

### Extraction Value for Indexers
HubCloud drive pages expose **ground-truth media properties** that may not be fully declared on upstream landing pages:
1. **Canonical Filename**: Preserves the exact scene/release tag (e.g. `(Movies4u.Foo).Ozark.S03E01...mkv`).
2. **Exact Byte/MB Size**: Discloses the exact file size (`234.84 MB`) rather than rounded estimates (`220MB`).
3. **MIME Container**: Identifies container format (`video/matroska` vs `video/mp4`).
4. **Exact Upload Timestamp**: Discloses when the file was registered on the locker network.

---

## 3. Intermediate Token & Redirector Tier (`gamerxyt.com`)

Rather than placing raw CDN download links directly in the HTML markup, HubCloud employs a dynamic token-generation mechanism in JavaScript:

```javascript
var url = 'https://gamerxyt.com/hubcloud.php?host=hubcloud&id=yx3i8todxvnv7j9&token=MS9nUjVXQWRpYlBsbE1XbE1yQmZ1MjlwQVRtTE5TMjBwM1FqOXcwWkVjRT0=';

setTimeout(function(){
    document.querySelector(".loading").classList.add("d-none");
    document.querySelector(".vd").classList.remove("d-none");

    if (false && !document.cookie.split(';').some(item => item.trim().startsWith('xlax='))) {
        stck('xlax', "s4t", 1440);
        window.location.href = url;
    }
}, 2000);
```

### Token Attributes
- `host`: Locker identity (`hubcloud`).
- `id`: File identifier (`yx3i8todxvnv7j9`).
- `token`: Base64-encoded cryptographic HMAC signature authorizing access to the intermediary gateway.
- `gamerxyt.com`: A dedicated bridge domain (also on Cloudflare) handling ad monetization verification, countdown timers, and final download stream generation.

---

## 4. Affiliated Domain Mesh

Inlined JavaScript configurations and historical comments inside HubCloud HTML reveal direct operational relationships with a network of domains:
- `abhilinks.life` / `abhilinks.site` (Upstream intermediary landing gateway)
- `m4ulinks.com` / `new.m4ulinks.com` (Historical / alternate link gateways)
- `movies4u.review` / `imovies4u.me` (Main syndication portals)
- `gamerxyt.com` (Monetization and redirect bridge)
