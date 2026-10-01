#!/usr/bin/env bash
set -e

# ==============================================================================
# BHILAI_TV // Ultra-Fast Cloud Run Redeployment Script
# ==============================================================================

SERVICE_NAME="bhilaitv"
REGION="${GCLOUD_REGION:-us-central1}"

# Optional 1-time setup flag: ./deploy-cloudrun.sh --setup
if [ "$1" == "--setup" ]; then
    echo ">> [1-TIME SETUP] Enabling Google Cloud APIs..."
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com
fi

echo "=========================================================="
echo "  BHILAI_TV // FAST CLOUD RUN REDEPLOY"
echo "=========================================================="
echo ">> Target Service : $SERVICE_NAME"
echo ">> Region         : $REGION"
echo ">> Building & streaming new revision to Cloud Run..."
echo ""

# Direct 1-step build and redeploy with zero prompts or redundant API calls
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
    --quiet

echo ""
echo "=========================================================="
LIVE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)' 2>/dev/null || true)
if [ -n "$LIVE_URL" ]; then
    echo "  [OK] LIVE CLOUD RUN URL: $LIVE_URL"
else
    echo "  [OK] DEPLOYMENT COMPLETED SUCCESSFULLY"
fi
echo "=========================================================="
