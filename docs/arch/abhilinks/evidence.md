# Evidence & Findings Log: AbhiLinks

## 1. Network & Infrastructure Evidence

### 1.1 DNS & Anycast Edge
- **Target Host**: `abhilinks.site`
- **Resolved IP Addresses**:
  - `172.67.201.204` (Cloudflare Anycast, AS13335)
  - `104.21.60.216` (Cloudflare Anycast, AS13335)
- **What it proves**: The site is protected by Cloudflare Edge Network. Origin server IP is masked behind Anycast reverse proxies.
- **Confidence**: **Confirmed**

### 1.2 TLS / SSL Certificate Details
- **Common Name (Subject)**: `abhilinks.site`
- **Subject Alternative Names (SAN)**: `abhilinks.site`, `*.abhilinks.site`
- **Issuer**: `Google Trust Services LLC` (`WE1 CA`, `US`)
- **Validity**: `Jul 8 09:03:25 2026 GMT` to `Oct 6 10:01:40 2026 GMT`
- **What it proves**: Cloudflare Universal SSL with GTS automated rotation is active.
- **Confidence**: **Confirmed**

---

## 2. HTTP Header Traces

### 2.1 Homepage Request (`GET /`)
```http
HTTP/2 200 
date: Tue, 01 Sep 2026 05:37:45 GMT
content-type: text/html; charset=UTF-8
link: <https://abhilinks.site/wp-json/>; rel="https://api.w.org/"
x-litespeed-cache-control: public,max-age=604800
x-litespeed-tag: 4b0_home,4b0_URL.6666cd76f96956469e7be39d750cc7d9,4b0_F,4b0_
server: cloudflare
alt-svc: h3=":443"; ma=86400
x-turbo-charged-by: LiteSpeed
cf-cache-status: DYNAMIC
nel: {"report_to":"cf-nel","success_fraction":0.0,"max_age":604800}
cf-ray: a341ecbd9e6473ab-MRS
```
- **What it proves**:
  - LiteSpeed Web Server is running with LSCache active (`x-turbo-charged-by: LiteSpeed`, `x-litespeed-tag`).
  - Cache TTL is set to 7 days (`max-age=604800`).
  - Cloudflare passes HTML requests to origin (`cf-cache-status: DYNAMIC`).
  - WordPress REST API is discoverable via `link` header.
- **Confidence**: **Confirmed**

### 2.2 Single Post Request (`GET /archives/42507/`)
```http
HTTP/2 200 
date: Tue, 01 Sep 2026 05:39:48 GMT
content-type: text/html; charset=UTF-8
x-litespeed-cache: hit
server: cloudflare
cf-cache-status: DYNAMIC
cf-ray: a341f09cde888a70-MRS
```
- **What it proves**: Single post pages are fully cached by LiteSpeed Cache (`x-litespeed-cache: hit`). Requests are served with near-zero origin compute latency.
- **Confidence**: **Confirmed**

### 2.3 WordPress REST API Request (`GET /wp-json/wp/v2/posts?per_page=3`)
```http
HTTP/2 200 
date: Tue, 01 Sep 2026 05:38:20 GMT
content-type: application/json; charset=UTF-8
x-wp-total: 15451
x-wp-totalpages: 5151
link: <https://abhilinks.site/wp-json/wp/v2/posts?per_page=3&page=2>; rel="next"
x-litespeed-cache-control: no-cache
cf-cache-status: DYNAMIC
server: cloudflare
cf-ray: a341eda18d9de183-MRS
```
- **What it proves**:
  - Database contains exactly **15,451 published posts**.
  - REST responses are uncached (`x-litespeed-cache-control: no-cache`), providing live catalog metrics.
  - Native RFC 5988 pagination headers are exposed.
- **Confidence**: **Confirmed**

---

## 3. Frontend & Theme Evidence

### 3.1 Theme Metadata (`GET /wp-content/themes/m4u/style.css`)
```css
/*!
Theme Name: m4u
Theme URI: http://underscores.me/
Author: Underscores.me
Author URI: http://underscores.me/
Description: Description
Version: 1.0.0
Tested up to: 5.4
Requires PHP: 5.6
License: GNU General Public License v2 or later
Text Domain: m4u
*/
```
- **What it proves**: The site runs a custom minimal child theme named `m4u` created on top of Automattic's Underscores (`_s`).
- **Confidence**: **Confirmed**

### 3.2 HTML Meta Generator Tag
```html
<meta name="generator" content="WordPress 7.1" />
```
- **What it proves**: The CMS core is WordPress (customized version identifier).
- **Confidence**: **Confirmed**

---

## 4. Evidence Matrix for Architectural Assertions

| Observation / Fact | Origin Evidence | What it Proves | What it Does Not Prove | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| **Total Post Count = 15,451** | Header `X-WP-Total: 15451` on `/wp/v2/posts` | The total number of published WordPress post objects. | Does not reveal draft, private, or trashed posts. | **Confirmed** |
| **No Media / Poster Uploads** | 0 `<img>` tags on homepage/archives; `featured_media: 0` | The site does not host movie posters or local image attachments. | Does not prove whether images were hosted in the past. | **Confirmed** |
| **Numeric Permalinks** | Post links format `/archives/<id>/` | Permalinks are configured to custom numeric IDs. | Does not prevent slug-based queries via REST. | **Confirmed** |
| **Download Lockers** | 100% of sampled buttons point to `hubcloud.cx` / `gdflix.dev` | The site delegates all storage and file delivery to external lockers. | Does not prove backend ownership of lockers. | **Confirmed** |
| **LiteSpeed Cache Origin** | `x-turbo-charged-by: LiteSpeed`, `x-litespeed-cache: hit` | Origin web server is LiteSpeed running LSCache module. | Does not disclose physical hosting provider/datacenter. | **Confirmed** |

---

## 5. Security & Defensive Hardening Findings

During the architectural investigation, several standard configuration exposures were noted. We provide the following hardening recommendations for web administrators:

### 1. REST API User Enumeration
- **Observation**: `/wp-json/wp/v2/users` exposes public author identities (`admin`, author IDs).
- **Risk**: Allows attackers to discover valid WordPress usernames for brute-force targeting.
- **Defensive Recommendation**: Restrict `/wp-json/wp/v2/users` to authenticated requests by adding a filter:
  ```php
  add_filter('rest_endpoints', function($endpoints) {
      if (isset($endpoints['/wp/v2/users']) && !is_user_logged_in()) {
          unset($endpoints['/wp/v2/users']);
      }
      return $endpoints;
  });
  ```

### 2. Generator Tag Exposure
- **Observation**: `<meta name="generator" content="WordPress 7.1" />` is broadcast in HTML heads.
- **Risk**: Broadcasts CMS version information to automated scanners.
- **Defensive Recommendation**: Remove the generator action in `functions.php`:
  ```php
  remove_action('wp_head', 'wp_generator');
  ```

### 3. XML Sitemap 404 Confusion
- **Observation**: XML sitemaps return 404 rather than an explicit empty index or redirect.
- **Defensive Recommendation**: If sitemaps are intentionally omitted, configure a clean robots directive and return standard headers to avoid unnecessary 404 crawler retries.
