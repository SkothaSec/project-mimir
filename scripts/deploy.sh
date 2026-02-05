#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -euo pipefail

# --- CONFIGURATION ---
# Get Project ID from gcloud config if not set
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
APP_NAME="mimir-processor"
REPO_NAME="mimir-repo"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/processor:latest"

# Directory setup (Find the root of the repo relative to this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
TERRAFORM_DIR="${ROOT_DIR}/infrastructure"

echo "=================================================="
echo "   DEPLOYING PROJECT MIMIR TO: ${PROJECT_ID}"
echo "=================================================="

# 1. INFRASTRUCTURE (Terraform)
echo ">>> [1/4] Checking Infrastructure..."
cd "${TERRAFORM_DIR}"
terraform init
terraform apply -auto-approve -var="project_id=${PROJECT_ID}"

# 2. BUILD (Docker)
# We force --platform linux/amd64 to ensure compatibility with Cloud Run
echo ">>> [2/4] Building Container Image..."
cd "${ROOT_DIR}"
# --no-cache ensures we don't accidentally use an old layer
docker build --no-cache --platform=linux/amd64 -t "${IMAGE_URI}" .

# 3. PUSH (Artifact Registry)
echo ">>> [3/4] Pushing to Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
docker push "${IMAGE_URI}"

# 4. DEPLOY (Cloud Run)
echo ">>> [4/4] Deploying Service to Cloud Run..."
gcloud run deploy "${APP_NAME}" \
  --image "${IMAGE_URI}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --set-env-vars "BQ_TABLE_ID=${PROJECT_ID}.mimir_security_lake.investigations_results" \
  --allow-unauthenticated

echo "=================================================="
echo "   DEPLOYMENT COMPLETE"
echo "=================================================="