# Search System Reverse-Engineering: AbhiLinks

## 1. Search Mechanisms Overview

AbhiLinks provides two distinct search interfaces:
1. **Frontend HTML Search**: Native WordPress query search via standard URL parameters.
2. **REST API Search Endpoints**: Native JSON REST query search supporting rich metadata filtering and pagination.

Neither third-party search engines (e.g., Elasticsearch, Algolia) nor heavy AJAX autocomplete search plugins (e.g., Relevanssi, Ajax Search Lite) are present. All search operations execute directly against the WordPress database query engine.

---

## 2. Frontend Search Architecture

### Request Endpoint & Parameters
- **URL**: `https://abhilinks.site/?s=<query>`
- **HTTP Method**: `GET`
- **Pagination Parameter**: `paged=<number>` (e.g., `https://abhilinks.site/?s=ozark&paged=2` or `/page/2/?s=ozark`)
- **RSS Feed for Search**: `https://abhilinks.site/search/<query>/feed/rss2/`

### Matching & Ranking Behavior
- **Query Execution**: Standard WordPress `WP_Query` executes SQL `LIKE '%<query>%'` against `post_title` and `post_content` in the `wp_posts` table.
- **Title Structure Match**: Because release titles follow strict naming conventions (e.g., `Title (Year) Season N Dual Audio Hindi ORG. + English WEB-DL 720p [Size]`), keyword searches for titles, years, languages, or resolutions reliably match against `post_title`.
- **Ranking**: Results are sorted chronologically (`post_date DESC`) by default.
- **Search Excerpt**: Because `post_content` is empty in database posts, search result cards display the post title and metadata headers.

---

## 3. REST API Search Endpoints

The WordPress REST API exposes two primary search mechanisms:

### Option A: Standard Posts Endpoint with Search Filter
- **Endpoint**: `GET /wp-json/wp/v2/posts?search=<query>`
- **Supported Parameters**:
  - `search`: The keyword string.
  - `per_page`: Number of results per page (1 to 100).
  - `page`: Page number offset.
  - `_fields`: Comma-separated list of fields to return (e.g., `id,title,slug,date,link`).
  - `order` / `orderby`: Sort order (`desc`, `asc`, `date`, `title`, `relevance`).
- **Response Headers**:
  - `X-WP-Total`: Total matching posts found.
  - `X-WP-TotalPages`: Total pages of results.
  - `Link`: RFC 5988 pagination relations (`rel="next"`, `rel="prev"`).
- **Example**:
  ```http
  GET /wp-json/wp/v2/posts?search=ozark&per_page=10&_fields=id,title,link HTTP/2
  Host: abhilinks.site
  ```
  ```json
  [
    {
      "id": 42507,
      "link": "https://abhilinks.site/archives/42507/",
      "title": {
        "rendered": "Ozark Season 3 Dual Audio Hindi ORG. + English Netflix Original WEB Series WEB-DL 480p [220MB/E]"
      }
    },
    {
      "id": 42505,
      "link": "https://abhilinks.site/archives/42505/",
      "title": {
        "rendered": "Ozark Season 3 Dual Audio Hindi ORG. + English Netflix Original WEB Series WEB-DL 720p [450MB/E]"
      }
    }
  ]
  ```

### Option B: Dedicated Search Index Endpoint
- **Endpoint**: `GET /wp-json/wp/v2/search?search=<query>`
- **Supported Parameters**: `search`, `per_page`, `page`, `type` (default: `post`), `subtype`.
- **Response Payload**: Ultra-lightweight JSON objects containing only search index attributes:
  ```json
  [
    {
      "id": 42507,
      "title": "Ozark Season 3 Dual Audio Hindi ORG. + English Netflix Original WEB Series WEB-DL 480p [220MB/E]",
      "url": "https://abhilinks.site/archives/42507/",
      "type": "post",
      "subtype": "post",
      "_links": { ... }
    }
  ]
  ```

---

## 4. Comparison of Search Approaches

| Feature / Metric | Frontend HTML (`/?s=`) | REST `/wp/v2/search` | REST `/wp/v2/posts?search=` |
| :--- | :--- | :--- | :--- |
| **Response Format** | Full HTML Document (~25 KB) | Minimal JSON (~1.2 KB) | Filterable JSON (~1.5 KB) |
| **Max Results Per Req**| 10 (fixed WP pagination) | 100 (`per_page=100`) | 100 (`per_page=100`) |
| **Pagination Metadata**| Parsed from HTML nav | `X-WP-Total` headers | `X-WP-Total` headers |
| **Parsing Overhead** | High (HTML scraping) | Very Low (JSON) | Very Low (JSON) |
| **Incremental Date Filter**| Not supported | Not supported | Supported (`after=`, `before=`) |
| **Field Customization**| None | Fixed schema | Supported via `_fields` |

---

## 5. Canonical & Most Efficient Search Strategy

When querying the site for specific content (rather than bootstrapping the entire inventory):
1. **Execute**: `GET /wp-json/wp/v2/posts?search=<query>&per_page=100&_fields=id,title,slug,date,link`
2. **Inspect Response**: Read `X-WP-Total` to determine if multiple pages exist.
3. **Resolve Links**: Fetch `/archives/<id>/` only for target matching IDs to extract download locker buttons.
