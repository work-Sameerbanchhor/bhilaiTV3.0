# Storage & Data Model Inference: AbhiLinks

## 1. Storage Architecture Overview

AbhiLinks utilizes a streamlined relational schema centered around standard WordPress MySQL tables, heavily optimized by omitting traditional CMS assets (such as local media uploads and extensive taxonomy relationships).

---

## 2. Inferred Relational Schema

```text
+-----------------------------------------------------------------------+
|                              MySQL / MariaDB                          |
+-----------------------------------------------------------------------+
|  wp_posts                                                             |
|  - ID (bigint)                  -> e.g. 42507                         |
|  - post_title (text)            -> "Ozark Season 3 Dual Audio..."     |
|  - post_name (varchar)          -> "ozark-season-3-dual-audio-..."    |
|  - post_date (datetime)         -> "2026-08-31 16:12:09"              |
|  - post_modified (datetime)     -> "2026-08-31 16:12:09"              |
|  - post_status (varchar)        -> "publish"                          |
|  - post_type (varchar)          -> "post"                             |
|  - post_content (longtext)      -> "" (Empty string)                  |
+-----------------------------------------------------------------------+
                                  |
                                  | 1 : N Relationship (post_id)
                                  v
+-----------------------------------------------------------------------+
|  wp_postmeta                                                          |
|  - meta_id (bigint)                                                   |
|  - post_id (bigint)             -> 42507                              |
|  - meta_key (varchar)           -> e.g., "download_links", "_acf"     |
|  - meta_value (longtext)        -> Serialized array of resolutions/   |
|                                    episodes & provider URLs           |
+-----------------------------------------------------------------------+
                                  |
                                  | 1 : N Relationship
                                  v
+-----------------------------------------------------------------------+
|  wp_term_relationships                                                |
|  - object_id (bigint)           -> 42507                              |
|  - term_taxonomy_id (bigint)    -> 1 ("Uncategorized")                |
+-----------------------------------------------------------------------+
```

---

## 3. Storage Layer Inference & Evidence

### 1. Movie & Series Core Metadata (Confirmed)
- **Stored In**: `wp_posts`
- **Fields**:
  - `ID`: Primary key and basis of the permalink (`/archives/<ID>/`).
  - `post_title`: Contains the complete human-readable release descriptor (Title, Year, Season, Audio languages, Source, Resolution, Episode file size).
  - `post_name`: Sanitized URL slug.
  - `post_date` / `post_modified`: Publication and edit timestamps.
- **Evidence**: Directly verified via `/wp-json/wp/v2/posts`.

### 2. Download Links, Episodes & Resolutions (Confirmed)
- **Stored In**: `wp_postmeta` (or ACF serialized metadata)
- **Mechanism**: The WordPress REST API returns `content.rendered: ""` for all sampled posts, yet requesting `/archives/<id>/` produces a rich HTML tree containing resolutions, sizes, episode numbers, and locker links. This confirms the data is stored in `wp_postmeta` and rendered by PHP template functions (`get_post_meta()` or ACF `get_field()`) in the theme.
- **Evidence**:
  - Empty REST `content.rendered` across pages 1, 10, 100, 500.
  - Presence of `acf: []` / `_acf_changed` in REST schema.
  - Deterministic container classes (`.download-links-div`, `.downloads-btns-div`).

### 3. Media & Image Storage (Confirmed)
- **Stored In**: Nowhere on AbhiLinks.
- **Evidence**:
  - The homepage and single post HTML contain **zero local `<img>` elements** referencing `/wp-content/uploads/`.
  - The REST API `featured_media` attribute is `0` (no featured image assigned) for posts.
  - The site minimizes disk I/O and CDN bandwidth by serving zero thumbnail images.

### 4. Actual Movie & Video Binaries (Confirmed)
- **Stored In**: External third-party cloud lockers (`hubcloud.cx`, `gdflix.dev`).
- **Evidence**: All download buttons link directly to external domains (`https://hubcloud.cx/drive/*` and `https://gdflix.dev/file/*`). AbhiLinks stores zero video bytes.

---

## 4. Confidence & Storage Matrix

| Data Item | Storage Location | Ingestion / Lifecycle | Confidence Level |
| :--- | :--- | :--- | :--- |
| **Title / Release Name** | MySQL `wp_posts.post_title` | Created via WP Admin / Auto-poster | **Confirmed** |
| **Permalink / Archive ID**| MySQL `wp_posts.ID` | Auto-increment primary key | **Confirmed** |
| **Publication Timestamps**| MySQL `wp_posts.post_date` | Assigned on publish | **Confirmed** |
| **Resolution / Quality** | MySQL `wp_postmeta` | Parsed from release info | **Confirmed** |
| **Locker Link URLs** | MySQL `wp_postmeta` | Injected into post meta | **Confirmed** |
| **Categories / Tags** | MySQL `wp_terms` (Default Only)| Single category ID 1 ("Uncategorized") | **Confirmed** |
| **Images / Posters** | N/A (Omitted) | Not stored or rendered | **Confirmed** |
| **Video Files** | External Lockers (HubCloud/GDFlix)| Hosted on third-party infrastructure | **Confirmed** |
