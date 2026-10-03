#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "mock-project")
REGION="us-central1"
SERVICE_NAME="agent-sandbox"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "Building Docker image..."
docker build -t "${IMAGE_TAG}" -f sandbox/Dockerfile sandbox

echo "Pushing Docker image to Google Container Registry..."
# In a real environment, we would push:
# docker push "${IMAGE_TAG}"

echo "Deploying to Cloud Run..."
# gcloud run deploy "${SERVICE_NAME}" \
#   --image "${IMAGE_TAG}" \
#   --region "${REGION}" \
#   --platform managed \
#   --allow-unauthenticated \
#   --memory 512MiB \
#   --cpu 0.5 \
#   --concurrency 1 \
#   --timeout 15s \
#   --execution-environment gen2 \
#   --set-env-vars SANDBOX_SECRET_KEY="super-secret-governance-key-12345"

echo "Deployment script completed successfully (dry-run/mock mode)."
