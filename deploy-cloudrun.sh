#!/usr/bin/env bash
set -e

# ==============================================================================
# BHILAI_TV // Google Cloud Run Deployment Script
# ==============================================================================

SERVICE_NAME="bhilaitv"
REGION="${GCLOUD_REGION:-us-central1}"

echo "=========================================================="
echo "  BHILAI_TV // GOOGLE CLOUD RUN DEPLOYMENT"
echo "=========================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "[!] Error: Google Cloud SDK (gcloud) is not found in PATH."
    echo "    Please install it: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo "[!] No active Google Cloud project selected."
    echo "    Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo ">> Active Project : $PROJECT_ID"
echo ">> Target Service : $SERVICE_NAME"
echo ">> Region         : $REGION"
echo ""

echo ">> Enabling Cloud Run and Cloud Build APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project "$PROJECT_ID"

echo ">> Building container and deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80 \
    --set-env-vars "ABHI_BASE_URL=https://abhilinks.site,MOVIESHUNT_BASE_URL=https://movieshunt.casa,HTTP_TIMEOUT=12.0" \
    --project "$PROJECT_ID"

echo ""
echo "=========================================================="
echo "  [SUCCESS] BHILAI_TV DEPLOYED TO GOOGLE CLOUD RUN!"
echo "=========================================================="
gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)' --project "$PROJECT_ID"
