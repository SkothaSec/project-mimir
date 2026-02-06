#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -euo pipefail

# --- CONFIGURATION ---
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
APP_NAME="mimir-processor"
REPO_NAME="mimir-repo"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/processor:latest"
TOPIC_NAME="mimir-ingest-topic"
SUB_NAME="mimir-ingest-sub"

# Directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
TERRAFORM_DIR="${ROOT_DIR}/infrastructure"

echo "=================================================="
echo "   DEPLOYING PROJECT MIMIR TO: ${PROJECT_ID}"
echo "=================================================="

# 1. INFRASTRUCTURE (Terraform)
echo ">>> [1/5] Checking Infrastructure..."
cd "${TERRAFORM_DIR}"
terraform init
terraform apply -auto-approve -var="project_id=${PROJECT_ID}"

# 2. BUILD (Docker) - skip if no relevant changes
echo ">>> [2/5] Building Container Image..."
cd "${ROOT_DIR}"
if git diff --quiet HEAD -- Dockerfile src requirements.txt client ; then
  echo "No Docker-relevant changes detected; skipping build/push."
  SKIP_PUSH=true
else
  docker build --platform=linux/amd64 -t "${IMAGE_URI}" .
  SKIP_PUSH=false
fi

# 3. PUSH (Artifact Registry)
if [ "${SKIP_PUSH}" = false ]; then
  echo ">>> [3/5] Pushing to Artifact Registry..."
  gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
  docker push "${IMAGE_URI}"
else
  echo ">>> [3/5] Skipping push (image unchanged)."
fi

# 4. DEPLOY (Cloud Run)
echo ">>> [4/5] Deploying Service to Cloud Run..."
gcloud run deploy "${APP_NAME}" \
  --image "${IMAGE_URI}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --set-env-vars "BQ_TABLE_ID=${PROJECT_ID}.mimir_security_lake.investigations_results" \
  --allow-unauthenticated

# 5. WIRING (Pub/Sub -> Cloud Run)
echo ">>> [5/5] Wiring Pub/Sub Subscription..."
# Get the URL of the just-deployed service
SERVICE_URL=$(gcloud run services describe "${APP_NAME}" --region "${REGION}" --format 'value(status.url)')

# Create or Update the Push Subscription
if ! gcloud pubsub subscriptions describe "${SUB_NAME}" --project "${PROJECT_ID}" &>/dev/null; then
  echo "Creating new subscription pointing to ${SERVICE_URL}..."
  gcloud pubsub subscriptions create "${SUB_NAME}" \
    --topic "${TOPIC_NAME}" \
    --push-endpoint "${SERVICE_URL}" \
    --ack-deadline 600 \
    --project "${PROJECT_ID}"
else
  echo "Updating existing subscription to ${SERVICE_URL}..."
  gcloud pubsub subscriptions update "${SUB_NAME}" \
    --push-endpoint "${SERVICE_URL}" \
    --project "${PROJECT_ID}"
fi

echo "=================================================="
echo "   DEPLOYMENT & WIRING COMPLETE"
echo "=================================================="
echo "Cloud Run URL: ${SERVICE_URL}"
echo "UI: ${SERVICE_URL}/ui"
