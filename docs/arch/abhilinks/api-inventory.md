# Public REST API Inventory: AbhiLinks

## 1. Overview & Root Discovery

AbhiLinks exposes the standard WordPress REST API v2 alongside LiteSpeed Cache REST endpoints. The API root is discoverable via the standard Link header:
```http
Link: <https://abhilinks.site/wp-json/>; rel="https://api.w.org/"
```

A discovery `GET` request to `https://abhilinks.site/wp-json/` returns the complete namespace and route schema containing **147 registered routes**.

---

## 2. API Namespaces

| Namespace | Origin / Component | Description |
| :--- | :--- | :--- |
| `wp/v2` | WordPress Core | Standard CRUD endpoints for posts, pages, categories, taxonomies, types, and search. |
| `litespeed/v1` | LiteSpeed Cache Plugin | Internal cache crawler and image notification endpoints. |
| `litespeed/v3` | LiteSpeed Cache Plugin | CDN status, ping, and IP validation endpoints. |
| `oembed/1.0` | WordPress Core oEmbed | Embed discovery and proxy endpoints for external consumers. |
| `wp-site-health/v1` | WordPress Core Health | Background diagnostic endpoints (restricted). |
| `wp-block-editor/v1` | WordPress Gutenberg | Block editor pattern and template endpoints. |
| `wp-abilities/v1` | WordPress Core | Capability validation endpoints. |

---

## 3. Useful Endpoints for Discovery & Indexing

| Endpoint | HTTP Method | Purpose | Response Data | Pagination Support | Useful for Indexing? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/wp/v2/posts` | `GET` | Retrieve list of published posts / movies / series | Post ID, title, date, modified, slug, link, status | Yes (`per_page=1..100`, `page=1..N`, `X-WP-Total`, `X-WP-TotalPages`) | **Highest Utility (Primary Indexing Endpoint)** |
| `/wp/v2/posts/(?P<id>[\d]+)` | `GET` | Retrieve single post metadata | Post ID, title, date, modified, slug, format | N/A (Single Item) | Moderate (does not expose custom postmeta) |
| `/wp/v2/search` | `GET` | Global search index across content | Array of `{id, title, url, type, subtype}` | Yes (`per_page`, `page`) | High (Fast keyword search) |
| `/wp/v2/types` | `GET` | Enumerate registered post types | Schema definition of post types (`post`, `page`, etc.) | None | High (Schema verification) |
| `/wp/v2/taxonomies` | `GET` | Enumerate registered taxonomies | Schema definition of taxonomies (`category`, `post_tag`) | None | Moderate (Taxonomy verification) |
| `/wp/v2/categories` | `GET` | List categories | Category list (`id: 1`, `uncategorized`, `count: 15451`) | Yes | Low (Only 1 uncategorized category used) |
| `/wp/v2/tags` | `GET` | List tags | Empty array (`count: 0`) | Yes | None (Tags not used) |
| `/oembed/1.0/embed` | `GET` | Retrieve oEmbed JSON for a post URL | Title, author, provider, html embed snippet | None | Low (Single URL lookup) |

---

## 4. REST API Query Parameters & Optimization

### Field Filtering (`_fields`)
The WordPress REST API natively supports field filtering to minimize response payloads and memory usage. By passing `_fields=id,date,modified,slug,title,link`, the JSON payload is reduced from ~3.5 KB per post to ~220 bytes per post (a **93.7% bandwidth reduction**).

### Filtering Parameters
- `per_page`: Accepts integers between `1` and `100` (default: 10). Maximum allowed is 100.
- `page`: 1-indexed page pointer.
- `after`: Restricts results to posts published after a specified ISO-8601 date-time string (e.g., `2026-08-30T00:00:00Z`).
- `modified_after`: Restricts results to posts modified after a specified timestamp.
- `order`: `asc` or `desc` (default: `desc`).
- `orderby`: `date`, `modified`, `id`, `title`, `slug`, `relevance`.

### Response Headers Reference
When querying paginated endpoints:
- `X-WP-Total`: Total count of records matching the query (`15451` on root posts query).
- `X-WP-TotalPages`: Total available pages (`155` when `per_page=100`).
- `Link`: Navigation relations (`<https://abhilinks.site/wp-json/wp/v2/posts?page=2>; rel="next"`).

---

## 5. Security & Access Control Analysis

- **Read Access**: All public `GET` endpoints are unauthenticated and unrestricted.
- **Write / Mutating Endpoints**: `POST`, `PUT`, `PATCH`, and `DELETE` methods on `/wp/v2/*` require WordPress cookie nonce authentication or application passwords (`/wp/v2/users/me/application-passwords`).
- **LiteSpeed Endpoints**: Diagnostic endpoints under `/litespeed/v1/` and `/litespeed/v3/` require IP validation or LiteSpeed API keys and reject unauthenticated requests.
