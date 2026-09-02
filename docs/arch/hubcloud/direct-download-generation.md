# Direct Download (DD) Link Generation: Deep Technical Analysis

## 1. End-to-End Direct Download Lifecycle

The generation of Direct Download (DD) links in the AbhiLinks / HubCloud ecosystem operates through a multi-stage, zero-trust tokenized pipeline. Direct storage URLs are never exposed statically on landing sites; instead, they are synthesized on-demand with cryptographic signatures and expiration windows.

```mermaid
sequenceDiagram
    autonumber
    actor Visitor as Browser Visitor
    participant Abhi as abhilinks.site (Gateway)
    participant Hub as hubcloud.cx (Locker Landing)
    participant Gate as gamerxyt.com (Link Synthesizer)
    participant R2 as Cloudflare R2 Object Storage (FSL)
    participant GPDL as gpdl.hubcloud.cx (10Gbps CDN)
    participant TG as Telegram Bot Storage

    Visitor->>Abhi: GET /archives/:id/
    Abhi-->>Visitor: Renders static button: https://hubcloud.cx/drive/:hash

    Visitor->>Hub: GET /drive/:hash
    Note over Hub: Edge Cache HIT (Cloudflare)
    Hub-->>Visitor: HTML with metadata + Base64 HMAC Token: var url = gamerxyt.com/hubcloud.php?...

    Visitor->>Gate: GET gamerxyt.com/hubcloud.php?host=hubcloud&id=:hash&token=:token
    Note over Gate: LiteSpeed PHP Engine validates HMAC Token & Timestamp
    Note over Gate: Generates AWS SigV4 Presigned URL + GPDL Token + TG Payload
    Gate-->>Visitor: HTML Page with Live Download Buttons

    alt Option A: FSL Server (Cloudflare R2 Object Storage)
        Visitor->>R2: GET r2.cloudflarestorage.com/hub/:hash?X-Amz-Algorithm=AWS4-HMAC-SHA256&...
        R2-->>Visitor: 200 OK / 206 Partial (Direct High-Speed Media Stream)
    else Option B: 10Gbps Dedicated Server (GPDL)
        Visitor->>GPDL: GET gpdl.hubcloud.cx/?id=:token_hex:::sig_hex
        GPDL-->>Visitor: 200 OK (Proxied CDN Media Stream)
    else Option C: Telegram Cloud Stream
        Visitor->>TG: GET hubcloud.cx/tg/go?id=:encrypted_payload
        TG-->>Visitor: Streaming chunk from Telegram Storage
    end
```

---

## 2. Detailed Technical Breakdown of Each Stage

### Stage 1: Static Hash Referencing (Gateway Tier)
- **Origin**: `abhilinks.site`
- **Mechanism**: The WordPress CMS stores a fixed 15-character alphanumeric token in `wp_postmeta` (e.g. `yx3i8todxvnv7j9`).
- **Exposure**: Rendered directly in HTML as `<a href="https://hubcloud.cx/drive/yx3i8todxvnv7j9">`.

### Stage 2: HMAC Session Token Generation (HubCloud Landing)
- **Origin**: `hubcloud.cx`
- **Mechanism**: When the drive page is rendered or fetched from Cloudflare edge cache, an inlined script creates a signed handoff URL:
  ```javascript
  var url = 'https://gamerxyt.com/hubcloud.php?host=hubcloud&id=yx3i8todxvnv7j9&token=MS9nUjVXQWRpYlBsbE1XbE1yQmZ1MjlwQVRtTE5TMjBwM1FqOXcwWkVjRT0=';
  ```
- **Token Anatomy**:
  - `host`: Identifies the originating locker service (`hubcloud`).
  - `id`: File identifier (`yx3i8todxvnv7j9`).
  - `token`: Base64-encoded HMAC-SHA256 signature containing creation timestamp and validation hash.

---

### Stage 3: Dynamic Direct Link Synthesis (`gamerxyt.com`)
- **Origin**: `gamerxyt.com/hubcloud.php` (powered by LiteSpeed PHP, `Cache-Control: no-store`).
- **Processing**:
  1. The PHP backend verifies the HMAC `token` against internal secrets.
  2. If the token is valid and unexpired, the server communicates with backend storage pools to generate **five concurrent direct download tiers**:

#### Tier 1: Cloudflare R2 Object Storage (FSL Server) — Primary Direct Download
- **Protocol**: S3-compatible REST API over HTTPS.
- **Synthesized URL Pattern**:
  ```text
  https://c357acb652b7e4cc192420afdff05f44.r2.cloudflarestorage.com/hub/e60fa92eedf994450a2d1201a85fb687
    ?X-Amz-Algorithm=AWS4-HMAC-SHA256
    &X-Amz-Credential=d6a0cd327387c6fca20391dfe93d98cf%2F20260901%2Fauto%2Fs3%2Faws4_request
    &X-Amz-Date=20260901T060723Z
    &X-Amz-Expires=28800
    &X-Amz-SignedHeaders=host
    &response-content-disposition=attachment%3B%20filename%3D%22(Movies4u.Foo).Ozark.S03E01.480p.WEB-DL.Hindi.English.ESub.x264.mkv%22
    &X-Amz-Signature=59e609ca0050e60f844322be150562f018fcc761e77ec7c3b08a63cabf970fe5
  ```
- **Security & Storage Design**:
  - **Bucket Storage**: Stored in Cloudflare R2 (`<account_hash>.r2.cloudflarestorage.com`).
  - **Signing Algorithm**: AWS Signature Version 4 (`AWS4-HMAC-SHA256`).
  - **Validity Window**: Exactly **8 hours** (`X-Amz-Expires=28800`).
  - **Content Disposition**: Forcibly triggers browser file download with the original release filename encoded.
  - **Zero-Egress Cost**: Leveraging Cloudflare R2's zero-data-egress-fee policy to serve multi-gigabyte video files at high bandwidth.

#### Tier 2: 10Gbps Dedicated CDN Server (GPDL)
- **Synthesized URL Pattern**:
  ```text
  https://gpdl.hubcloud.cx/?id=1e817c7f6b49669ea9e924aa3f48ac4a881915867c5d1f63bad9b334a513abb6109be87420baef68359ccf6ee8b201025187a963b01a7b62e8efc0598c3a06af487f6b77a26c52eb6738b188da946fefde9db74ddbf48811c474adf9665cca11390577d8e6519781d94a72fca52e1965::f21330f9177cfb34a0b189243648e2d8
  ```
- **Mechanism**: Dedicated streaming cluster (`gpdl.hubcloud.cx`) utilizing custom 128-byte hexadecimal tokens carrying cryptographic routing instructions.

#### Tier 3: Third-Party Fast Mirrors
- **PixelServer**: `https://pixeldrain.dev/u/<shortcode>`
- **Buzz Server**: `https://fuckingfast.net/<token>`

#### Tier 4: Telegram Cloud Stream
- **Synthesized URL Pattern**:
  ```text
  https://hubcloud.cx/tg/go?id=3Ofp3dyuoqThzuDY3N/K4aHZ3NCju+rPzODi6tHh2NXk4ajn59bf3bHDyp6uyN3Ht7u5qKrHmcbDwp2/qsq5w9PKuKqhwMvjw8fU5OTJ17O+xbqd48jL5bu2pKS6wcHYucuy4LE=
  ```
- **Mechanism**: Encrypted Base64 payload containing channel ID and Telegram `message_id` allowing direct chunked media streaming.

---

## 3. GDFlix Direct Link Generation Architecture

GDFlix follows an alternative Google Drive authorization pipeline:

1. **Client Proof-of-Work**: Browser solves Cloudflare Turnstile token on `gdflix.dev`.
2. **Service Account Rotation**: The GDFlix application pool maintains hundreds of Google Cloud service account keys (`credentials.json`).
3. **Download Token Creation**:
   - The service issues a request to `https://www.googleapis.com/drive/v3/files/<gdrive_file_id>?supportsAllDrives=true` with a service account OAuth2 token.
   - If the public quota is saturated, it invokes the Google Drive copy API (`files.copy`) to duplicate the media object into an active service account's Google Drive storage.
   - Generates a transient download URL (`https://drive.google.com/uc?export=download&id=...&confirm=...`) or pipes the media stream through a worker reverse-proxy.

---

## 4. Key Architectural Conclusions

1. **Decoupled Architecture**: Landing portals (`abhilinks.site`) never interact directly with binary storage. They deal exclusively with abstract IDs.
2. **Stateless CDN Scalability**: By using **Cloudflare R2 S3 SigV4 presigned URLs**, the system achieves unlimited direct download scaling without saturating origin web servers.
3. **Time-Limited Tokenization**: Direct links expire within 8 hours, preventing long-term hotlinking by unauthorized third-party crawlers.
