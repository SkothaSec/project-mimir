#!/usr/bin/env bash
set -euo pipefail

# Required env vars
: "${PROJECT_ID:?Set PROJECT_ID}"
: "${REGION:=us-central1}"
: "${SERVICE_NAME:=mimir-api}"
: "${IMAGE_NAME:=mimir-app}"
export TF_VAR_project_id="${PROJECT_ID}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TERRAFORM_DIR="${ROOT_DIR}/infrastructure"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/mimir-repo/${IMAGE_NAME}:latest"

echo ">>> Enabling required Google Cloud APIs via Terraform..."
cd "${TERRAFORM_DIR}"
terraform init
terraform apply -auto-approve

echo ">>> Building Docker image ${IMAGE_URI}..."
cd "${ROOT_DIR}"
docker build --platform=linux/amd64 -t "${IMAGE_URI}" .

echo ">>> Pushing image..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" -q
docker push "${IMAGE_URI}"

echo ">>> Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --region "${REGION}" \
  --no-allow-unauthenticated \
  --set-env-vars "BQ_TABLE_ID=${PROJECT_ID}.mimir_security_lake.investigations_results" \
  --port 8080 \
  --platform managed

echo ">>> Deployment complete."
