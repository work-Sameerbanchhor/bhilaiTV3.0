# Google Cloud Run Deployment Guide // BhilaiTV

This guide explains how to deploy **BhilaiTV** to **Google Cloud Run** with serverless auto-scaling, scale-to-zero cost savings, and high availability.

---

## 1. Why Google Cloud Run for BhilaiTV?

- **Scale to Zero**: When nobody is browsing, instances scale down to 0, meaning **$0 idle cost**.
- **Generous Free Tier**: Google Cloud Run includes **2 Million free requests per month** and 360,000 GB-seconds of memory free.
- **Serverless Containers**: No server maintenance, automatic SSL certificate provisioning, and global Anycast CDN.
- **Instant Scaling**: Automatically scales up under concurrent traffic (up to 80 concurrent users per instance).

---

## 2. Prerequisites

1. **Google Cloud SDK (`gcloud`)**: Installed and logged in (`gcloud auth login`).
2. **GCP Project**: An active Google Cloud Project with billing enabled.
3. **Artifact Registry / Cloud Build**: Automatically enabled by the deployment script.

---

## 3. Quick 1-Command Deployment

We have included an automated deployment script in the project root:

```bash
./deploy-cloudrun.sh
```

Or deploy directly with the `gcloud` CLI:

```bash
gcloud run deploy bhilaitv \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 80 \
  --set-env-vars "ABHI_BASE_URL=https://abhilinks.site,MOVIESHUNT_BASE_URL=https://movieshunt.casa,HTTP_TIMEOUT=12.0"
```

> **Note**: Google Cloud Build compiles the Docker container directly in the cloud from your source files. You do **not** need Docker installed locally on your machine.

---

## 4. Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Container port injected dynamically by Cloud Run |
| `HOST` | `0.0.0.0` | Listen host interface |
| `ABHI_BASE_URL` | `https://abhilinks.site` | Upstream WordPress catalog gateway |
| `MOVIESHUNT_BASE_URL` | `https://movieshunt.casa` | Upstream poster and artwork mirror |
| `HTTP_TIMEOUT` | `12.0` | Timeout in seconds for upstream HTTP requests |
| `MAX_PER_PAGE` | `50` | Maximum catalog results per page |

To update environment variables at any time without rebuilding:

```bash
gcloud run services update bhilaitv \
  --region us-central1 \
  --update-env-vars "HTTP_TIMEOUT=15.0"
```

---

## 5. Custom Domain Setup (e.g. `tv.sameerbanchhor.in`)

To map your custom domain to your Cloud Run service:

1. In Google Cloud Console, navigate to **Cloud Run** > **Custom Domain Mappings**.
2. Or use the CLI:
   ```bash
   gcloud beta run domain-mappings create \
     --service bhilaitv \
     --domain tv.sameerbanchhor.in \
     --region us-central1
   ```
3. Add the DNS records (`CNAME` or `A`/`AAAA`) provided by Google Cloud to your DNS provider (Cloudflare, Namecheap, Route53, etc.).
4. Google Cloud will automatically provision a free Managed SSL certificate within 15–30 minutes.

---

## 6. Live Logs & Telemetry

To stream live logs directly in your terminal:

```bash
gcloud run services logs tail bhilaitv --region us-central1
```

To view service status and URL:

```bash
gcloud run services describe bhilaitv --region us-central1 --format 'value(status.url)'
```

---

## 7. Local Testing with Docker (Optional)

If you have Docker or Colima installed locally:

```bash
# Build local container
docker build -t bhilaitv:local .

# Run container matching Cloud Run environment
docker run -p 8080:8080 -e PORT=8080 bhilaitv:local
```

Access at `http://localhost:8080`.
