# Sitemaps, Feeds & Crawler Directives: AbhiLinks

## 1. Robots.txt Analysis

The `robots.txt` file at `https://abhilinks.site/robots.txt` is actively served and managed via Cloudflare Managed Content rules combined with standard WordPress directives.

### Full Robots.txt Content

```text
# As a condition of accessing this website, you agree to abide by the following
# content signals:

# (a)  If a Content-Signal = yes, you may collect content for the corresponding use.
# (b)  If a Content-Signal = no, you may not collect content for the corresponding use.
# (c)  If the website operator does not include a Content-Signal for a corresponding use,
#      the website operator neither grants nor restricts permission via Content-Signal with
#      respect to the corresponding use.

# The content signals and their meanings are:
# search:   building a search index and providing search results (e.g., returning
#           hyperlinks and short excerpts from your website's contents). Search does not
#           include providing AI-generated search summaries.
# ai-input: inputting content into one or more AI models.
# ai-train: training or fine-tuning AI models.
# use:      how AI systems may consume the content (immediate, reference, or full).

# ANY RESTRICTIONS EXPRESSED VIA CONTENT SIGNALS ARE EXPRESS RESERVATIONS OF
# RIGHTS UNDER ARTICLE 4 OF THE EUROPEAN UNION DIRECTIVE 2019/790 ON COPYRIGHT
# AND RELATED RIGHTS IN THE DIGITAL SINGLE MARKET.

# BEGIN Cloudflare Managed content

User-agent: *
Content-Signal: search=yes,ai-train=no,use=reference
Allow: /

User-agent: Amazonbot
Disallow: /

User-agent: Applebot-Extended
Disallow: /

User-agent: Bytespider
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: CloudflareBrowserRenderingCrawler
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: GPTBot
Disallow: /

User-agent: meta-externalagent
Disallow: /

# END Cloudflare Managed Content

User-agent: *
Disallow: /wp-admin/
Allow: /wp-admin/admin-ajax.php
```

### Key Directives & Observations
1. **Search Indexing Explicitly Permitted**: The `Content-Signal` explicitly states `search=yes,use=reference` for general user agents, with `Allow: /`.
2. **AI Crawler Restrictions**: Explicit `Disallow: /` blocks are declared for known automated AI scrapers (`Amazonbot`, `Applebot-Extended`, `Bytespider`, `CCBot`, `ClaudeBot`, `GPTBot`, `meta-externalagent`, `Google-Extended`).
3. **No Sitemap Reference**: The `robots.txt` does not include a `Sitemap:` directive.

---

## 2. XML Sitemap Investigation

We tested all standard WordPress and SEO plugin sitemap paths:

| URL Endpoint | Expected Plugin / Engine | HTTP Status | Response Payload |
| :--- | :--- | :--- | :--- |
| `https://abhilinks.site/sitemap.xml` | Yoast SEO / RankMath / All-in-One SEO | `404 Not Found` | HTML Error Page |
| `https://abhilinks.site/sitemap_index.xml` | Yoast SEO / RankMath | `404 Not Found` | HTML Error Page |
| `https://abhilinks.site/wp-sitemap.xml` | WordPress Core Native XML Sitemaps | `404 Not Found` | HTML Error Page |
| `https://abhilinks.site/post-sitemap.xml` | Standard Post Sitemap | `404 Not Found` | HTML Error Page |

### Root Cause Analysis
- WordPress native XML sitemaps (`wp-sitemap.xml`) were introduced in WP 5.5. Their `404` status confirms they have been explicitly disabled via `add_filter('wp_sitemaps_enabled', '__return_false');` in the `m4u` theme's `functions.php` or a snippet.
- No third-party SEO plugins (Yoast, RankMath, AIOSEO) are installed.
- **Conclusion**: Standard XML sitemap discovery is non-functional on this site.

---

## 3. Syndication & RSS Feeds

While XML sitemaps are disabled, standard WordPress syndication feeds are fully functional and updated in real time:

| Feed Endpoint | Protocol / Standard | Content | Update Cadence |
| :--- | :--- | :--- | :--- |
| `https://abhilinks.site/feed/` | RSS 2.0 XML | 10 most recent posts with title, link, GUID, and pubDate | Real-time on publish |
| `https://abhilinks.site/feed/rss2/` | RSS 2.0 XML | Alias of `/feed/` | Real-time on publish |
| `https://abhilinks.site/feed/atom/` | Atom 1.0 XML | 10 most recent posts with ISO timestamps | Real-time on publish |
| `https://abhilinks.site/comments/feed/` | RSS 2.0 XML | Site-wide comments feed | Real-time |
| `https://abhilinks.site/search/<query>/feed/rss2/`| RSS 2.0 XML | Query-specific search results feed | Real-time |

### Sample RSS Item Structure

```xml
<item>
    <title>Ozark Season 3 Dual Audio Hindi ORG. + English Netflix Original WEB Series WEB-DL 480p [220MB/E]</title>
    <link>https://abhilinks.site/archives/42507/</link>
    <comments>https://abhilinks.site/archives/42507/#respond</comments>
    <dc:creator><![CDATA[admin]]></dc:creator>
    <pubDate>Mon, 31 Aug 2026 16:12:09 +0000</pubDate>
    <category><![CDATA[Uncategorized]]></category>
    <guid isPermaLink="false">https://abhilinks.site/?p=42507</guid>
    <description><![CDATA[]]></description>
</item>
```

---

## 4. Discovery Strategy Comparison: Sitemaps vs REST vs RSS

| Discovery Mechanism | Availability | Catalog Coverage | Granularity | Requests for 15,451 Posts | Incremental Capability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **XML Sitemaps** | ❌ Disabled (`404`) | 0% | None | N/A | None |
| **RSS Feed (`/feed/`)** | ✅ Active | Latest 10 posts (~0.06%) | High (Title, Date, Link) | 1 request | Excellent for real-time monitoring |
| **REST API (`/wp/v2/posts`)** | ✅ Active | 100% (15,451 posts) | Complete (ID, Title, Date, Slug) | **155 requests** | Excellent via `after=<timestamp>` |
| **HTML Archive Crawl** | ✅ Active | 100% | Full HTML | 1,546 requests (at 10/page) | Moderate |

### Recommendation
- **Initial Inventory**: Use the **REST API** (`/wp-json/wp/v2/posts?per_page=100&_fields=id,date,modified,slug,title,link`).
- **Real-Time Feed**: Poll `/feed/` every 5–15 minutes to discover newly published releases with a single lightweight HTTP request.
