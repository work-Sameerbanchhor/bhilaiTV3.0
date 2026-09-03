# BHILAI_TV // High-Performance Zero-Ad Media Discovery Engine

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-Serverless-4285F4?style=flat-square&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

> **Live Deployment:** [https://bhilaitv-23241707890.us-central1.run.app](https://bhilaitv-23241707890.us-central1.run.app)  
> **Global Anycast URL:** [https://bhilaitv-7ksu2o5y6q-uc.a.run.app](https://bhilaitv-7ksu2o5y6q-uc.a.run.app)

---

## 1. Executive Summary

**BhilaiTV** is an ultra-lightweight, high-concurrency media aggregation engine and streaming discovery gateway designed with a minimalist Unix terminal and cyberpunk CRT aesthetic. It eliminates intrusive advertisements, redirects, captchas, and multi-step locker traps by autonomously resolving clean, direct-download links and high-bandwidth Content Delivery Network (CDN) streams server-side.

Engineered with asynchronous Python (`FastAPI`), custom TLS fingerprint impersonation (`curl_cffi`), persistent HTTP/2 connection pooling, bounded in-memory caching, and zero frontend runtime dependencies, BhilaiTV achieves sub-millisecond local response times while running serverless at near-zero operating costs on Google Cloud Run.

---

## 2. Key Capabilities & Architectural Highlights

###  Server-Side Zero-Ad Link Resolvers
- **Server 1 (HubCloud Resolver):** Automatically navigates intermediary handshakes, extracting direct Cloudflare R2 presigned download streams, 10Gbps high-speed CDN URLs, PixelDrain mirrors, and Telegram stream links.
- **Server 2 (GDFlix / FastCloud Resolver):** Employs Chrome 120 TLS JA3/JA4 fingerprint impersonation (`curl_cffi`) to seamlessly bypass Cloudflare Turnstile bot detection and retrieve raw resumable FastCloud and ZipDisk streams.

###  Intelligent Title & Metadata Parsing Engine
- Strips language noise, dubbing descriptors, and distribution network tags (`Amazon Prime`, `Multi Audio`, `Complete WEB Series`) into clean canonical titles (e.g. `Reacher`).
- Distinguishes between **Movies** and **Episodic Series**, tagging season indices, explicit resolution tiers (`4K 2160P`, `1080P HQ`, `1080P`, `720P`, `480P`), audio tracks, and file sizes (`[650MB/E]` vs total movie payload `[2.4GB]`).

###  Automated Series Sibling Quality Discovery
- In typical release sites, episodic television seasons are published as separate standalone posts for each resolution tier (`480p`, `720p`, `1080p`, `4K`).
- BhilaiTV detects series releases and automatically queries sibling resolution tiers in the background, rendering an interactive switcher inside the drawer so users can toggle qualities seamlessly without leaving the modal.

###  Dynamic Artwork & TMDB Poster Integration
- Asynchronously aggregates pristine artwork directly from TMDB via upstream sister networks.
- Enforces bandwidth-optimized image scaling (`/w342/` for mobile and desktop grid cards, `~25KB` payload vs `~5MB` raw assets).
- Fully toggleable via CLI (`/posters on` and `/posters off`) or the settings drawer for pure high-density text terminal mode.

###  Interactive Terminal CLI & Command Shell
Includes an integrated command parser supporting slash commands with auto-completion and fuzzy matching:
- `/posters <on|off>`: Toggle between visual Netflix-style poster cards and ultra-dense text terminal mode.
- `/theme <0|matrix|amber|cyan|magenta>`: Switch CRT color palettes (`0` for Pure Monochrome B&W).
- `/filter <1080p|720p|4k|hindi|clear>`: Dynamic client-side release filter.
- `/settings`: Configure preferred default server (Server 1 vs Server 2) and page density.
- `/stats`: Inspect gateway health, latency telemetry, and resolver status.
- `/help`: Render the interactive keyboard cheat sheet.

###  Dual Adaptive Interfaces (Desktop Cinema & Mobile App)
- **Desktop:** Multi-column cinema browser with hover zoom effects, CRT scanline toggles, and drawer modals.
- **Mobile (iOS / Android):** Native streaming app experience with a 2-column poster grid, touch gesture dismissal, and fixed bottom drawers.

---

## 3. Technology Stack & Frameworks

```
┌───────────────────────────────────────────────────────────┐
│                    CLIENT / FRONTEND                      │
│   Vanilla ES6+ JS  •  CSS3 Custom Properties  •  HTML5    │
│   (0kB Framework Overhead  •  Under 40kB Total Bundle)    │
└─────────────────────────────┬─────────────────────────────┘
                              │ HTTP/2 / REST / JSON (GZip)
┌─────────────────────────────▼─────────────────────────────┐
│                    BACKEND APPLICATION                    │
│   FastAPI (ASGI)  •  Pydantic v2  •  Uvicorn (uvloop)     │
├───────────────────────────────────────────────────────────┤
│   - Connection Pool Manager (httpx with Keep-Alive)       │
│   - TLS JA3/JA4 Impersonation Engine (curl_cffi)          │
│   - Multi-Tier In-Memory LRU Cache (Capped at 1,000 Keys) │
│   - GZip Response Compression Middleware                  │
│   - Input Validation & Path Traversal Guards              │
└─────────────────────────────┬─────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────┐
│                 INFRASTRUCTURE & RUNTIME                  │
│   Google Cloud Run  •  Google Cloud Build  •  Docker      │
│   (Scale-to-Zero  •  Auto-Scaling  •  Non-Root Security)  │
└───────────────────────────────────────────────────────────┘
```

| Layer | Component | Description / Rationale |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance asynchronous REST API framework with native OpenAPI documentation and type validation. |
| **ASGI Web Server** | [Uvicorn](https://www.uvicorn.org/) + `uvloop` | Lightning-fast asynchronous server implementation utilizing libuv for event-loop throughput. |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) | Rust-backed data parsing and serialization ensuring strict schema validation. |
| **HTTP Client** | [HTTPX](https://www.python-httpx.org/) | Async HTTP/1.1 and HTTP/2 client configured with persistent connection pooling. |
| **TLS Impersonation** | [curl_cffi](https://github.com/yifeikong/curl_cffi) | Bypasses Cloudflare Turnstile bot detection via native browser TLS fingerprinting. |
| **Frontend Runtime** | Vanilla ES6+ & CSS3 | Zero frontend framework bloat (no React, Vue, or Angular bundle overhead), ensuring instant First Contentful Paint. |
| **Compression** | `GZipMiddleware` | Automatically compresses outgoing JSON and static responses exceeding 1KB by ~70%. |
| **Containerization** | [Docker](https://www.docker.com/) | Multi-stage Debian slim container executing under an unprivileged user (`appuser:10001`). |
| **Cloud Hosting** | [Google Cloud Run](https://cloud.google.com/run) | Serverless managed container platform with scale-to-zero capability ($0 idle cost). |

---

## 4. Performance & Optimization Engineering

BhilaiTV has been audited and hardened under heavy concurrent traffic. Here is why the system operates with exceptional speed:

### 1. Persistent Connection Pooling & Socket Reuse
Traditional scrapers instantiate a new HTTP client per request, incurring `300ms–500ms` of TCP and TLS handshake overhead on every call. BhilaiTV implements an event-loop-aware persistent client pool (`limits=httpx.Limits(max_keepalive_connections=25, max_connections=60)`). Reusing open keep-alive connections reduces upstream API response latency by **~40%**.

### 2. Bounded In-Memory Micro-Caching (Zero Memory Leak)
All release details, direct locker links, and TMDB posters are cached in memory using an LRU eviction policy capped at `MAX_CACHE_ENTRIES = 1000`:
- **Repeat Hits:** Sub-millisecond response (`<1ms`).
- **Memory Safety:** When capacity is reached, the oldest 20% of entries are purged, guaranteeing RAM stability during 24/7 continuous operation.

### 3. Asynchronous Batch Enrichment (`asyncio.gather`)
When catalog pages or search queries are retrieved, missing posters and sibling qualities are dispatched in parallel rather than sequentially. A page of 20 releases resolves in under **0.99 seconds** across all assets.

### 4. Bandwidth & Image Optimization
Rather than forwarding large multi-megabyte poster images, TMDB image URLs are automatically mapped to `/w342/` WebP/JPEG thumbnails (~25KB each), reducing client data consumption by over **95%** on mobile devices.

### 5. Production Concurrency Benchmark Results
Stress testing performed with 100 concurrent requests across various endpoints:

```text
=================================================================
  BHILAI_TV // PRODUCTION BENCHMARKS & CONCURRENCY AUDIT
=================================================================
  • 25 Concurrent /api/latest Requests       : 100% PASS (Avg: 2.9s under cold pool)
  • 25 Concurrent Multi-Query Searches       : 100% PASS (Avg: 2.0s)
  • 15 Concurrent Sibling Resolver Lookups   : 100% PASS (Avg: 1.7s)
  • 30 Concurrent Poster Lookups             : 100% PASS (Avg: 151.6ms | Min: 20.7ms)
  • Security & Path Traversal Fuzzing        : 100% BLOCKED (0 Crashes, 0 Leaks)
  • Automated Regression Unit Test Suite     : 12/12 PASSED (100%)
=================================================================
```

---

## 5. REST API Documentation

### `GET /api/health`
Health-check endpoint for Cloud Run uptime monitoring.
```json
{
  "status": "ONLINE",
  "service": "BhilaiTV Backend",
  "version": "1.0.0"
}
```

### `GET /api/latest?page=1&per_page=24`
Retrieves paginated latest movie and series releases with pre-parsed metadata and TMDB poster URLs.

### `GET /api/search?q={query}&page=1&per_page=24`
Searches upstream releases matching the query string.

### `GET /api/release/{post_id}`
Retrieves complete release information, including:
- Parsed clean title, season, quality, and size.
- Available direct locker buttons for movies.
- Episode-by-episode locker breakdown for series.
- Discovered sibling qualities (`sibling_qualities`) for 1-click resolution switching.

### `GET /api/poster?title={clean_title}`
Fast on-demand endpoint resolving official TMDB artwork URLs.

### `GET /api/resolve/direct?url={hubcloud_url}`
Server-side resolver for HubCloud URLs. Extracts direct Cloudflare R2 presigned download links, 10Gbps CDN streams, and PixelDrain mirrors.

### `GET /api/resolve/gdflix?url={gdflix_url}`
Server-side resolver for GDFlix links using Chrome TLS impersonation to bypass Turnstile and extract FastCloud/ZipDisk direct streams.

---

## 6. Quickstart & Local Development

### Prerequisites
- Python 3.11 or higher
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/work-Sameerbanchhor/bhilaiTV3.0.git
cd bhilaiTV3.0

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Running the Development Server

```bash
# Using Makefile
make dev

# Or directly via Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at `http://localhost:8000`.

### Running Automated Tests

```bash
# Run full test runner (parsers, endpoints, live resolvers)
make test

# Run production concurrency and security stress test
make stress
```

---

## 7. Google Cloud Run Deployment

BhilaiTV is designed for 1-command serverless deployment to Google Cloud Run:

```bash
# Deploy to Google Cloud Run
make deploy
```

*or directly using the deployment script:*

```bash
./deploy-cloudrun.sh
```

### Useful Makefile Automation Commands

| Command | Action |
|---|---|
| `make deploy` | Non-interactive 1-step Cloud Run build & deployment |
| `make logs` | Tail live production container logs in real time |
| `make status` | Check service revision, readiness status, and URL |
| `make test` | Run the 12-test regression test suite |
| `make stress` | Run the 100-request concurrency & security stress suite |
| `make dev` | Start local development server with hot-reload |

Refer to [`docs/CLOUD_RUN_DEPLOYMENT.md`](docs/CLOUD_RUN_DEPLOYMENT.md) for custom domain mapping (`tv.sameerbanchhor.in`), DNS setup, and environment variable tuning.

---

## 8. License

This project is licensed under the terms of the **MIT License**. See the [`LICENSE`](LICENSE) file for complete details.

```text
MIT License
Copyright (c) 2026 Sameer Banchhor
```
