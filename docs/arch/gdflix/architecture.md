# GDFlix Architecture & Technical Mechanics

## 1. Network & Security Topology

### Cloudflare Managed Challenge Tier
- **Host**: `gdflix.dev`
- **Anycast IPs**: `104.21.52.244`, `172.67.205.213` (Cloudflare AS13335)
- **SSL / TLS**: Google Trust Services LLC (WE1 CA) Universal SSL.
- **WAF Enforcement**:
  - GDFlix enforces **Cloudflare Managed Challenge / Super Bot Fight Mode** across its entire domain.
  - Raw HTTP `GET` requests without an interactive browser runtime, cookie store, and Turnstile execution return `HTTP 403 Forbidden` with the Cloudflare challenge document:
    ```html
    <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>
    ...
    <script src="https://challenges.cloudflare.com/turnstile/..."></script>
    ```

---

## 2. Inferred Backend Quota Balancing Mechanics

GDFlix belongs to the standard class of **Google Drive proxy engines** (similar to GDToT, DriveLink, or AppDrive).

### Operational Workflow
1. **Source Storage**: Media files are hosted on Google Drive using automated uploader scripts.
2. **Quota Circumvention**:
   - Google Drive imposes a 24-hour download bandwidth limit on public file shares.
   - When a user requests a file via GDFlix, the backend service uses a pool of Google Service Accounts (service account rotation) to clone/copy the file into a temporary Google Drive space or generate an authorization token.
3. **Delivery Modes**:
   - **Direct Google Drive Download**: Authenticated redirect to `drive.google.com/uc?export=download&id=...` using transient bearer tokens.
   - **Worker Proxy Stream**: Proxied streaming via Cloudflare Workers or intermediate VPS instances.

---

## 3. Comparison Between HubCloud and GDFlix

| Characteristic | HubCloud (`hubcloud.cx`) | GDFlix (`gdflix.dev`) |
| :--- | :--- | :--- |
| **Primary Focus** | Direct Download (DD) & Fast Cloud Locker | Google Drive Quota Bypassing / Proxy |
| **Public Metadata Exposure** | **High** (Exposes filename, size, container, date in HTML) | **Low** (Hidden behind Cloudflare Challenge) |
| **Edge Caching** | Cloudflare `cf-cache-status: HIT` | Dynamic Challenge Processing |
| **Next-Hop Flow** | Tokenized redirect to `gamerxyt.com` | Internal Google Drive auth generation |
| **Indexer Feasibility** | **Accessible** via standard HTTP GET | **Restricted** by Cloudflare Challenge |
