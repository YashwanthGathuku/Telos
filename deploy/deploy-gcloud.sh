#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="${1:?Usage: deploy-gcloud.sh <PROJECT_ID>}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-telos-orchestrator}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

WINDOWS_MCP_HOST="${WINDOWS_MCP_HOST:-}"
WINDOWS_MCP_PORT="${WINDOWS_MCP_PORT:-8083}"
SCREENSHOT_ENGINE_HOST="${SCREENSHOT_ENGINE_HOST:-}"
SCREENSHOT_ENGINE_PORT="${SCREENSHOT_ENGINE_PORT:-8085}"
FIRESTORE_COLLECTION="${FIRESTORE_COLLECTION:-telos_tasks}"
TELOS_PRIVACY_MODE="${TELOS_PRIVACY_MODE:-balanced}"
TELOS_ALLOW_IMAGE_EGRESS="${TELOS_ALLOW_IMAGE_EGRESS:-true}"

if [[ -z "${WINDOWS_MCP_HOST}" || -z "${SCREENSHOT_ENGINE_HOST}" ]]; then
  echo "Warning: WINDOWS_MCP_HOST and SCREENSHOT_ENGINE_HOST are not set."
  echo "Cloud Run will deploy, but it will not be able to drive a live desktop until those are configured."
fi

ENV_VARS="TELOS_PROVIDER=gemini,GEMINI_MODEL=gemini-2.0-flash,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},TELOS_MEMORY_BACKEND=firestore,FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION},TELOS_PRIVACY_MODE=${TELOS_PRIVACY_MODE},TELOS_ALLOW_IMAGE_EGRESS=${TELOS_ALLOW_IMAGE_EGRESS},WINDOWS_MCP_PORT=${WINDOWS_MCP_PORT},SCREENSHOT_ENGINE_PORT=${SCREENSHOT_ENGINE_PORT}"

if [[ -n "${WINDOWS_MCP_HOST}" ]]; then
  ENV_VARS="${ENV_VARS},WINDOWS_MCP_HOST=${WINDOWS_MCP_HOST}"
fi

if [[ -n "${SCREENSHOT_ENGINE_HOST}" ]]; then
  ENV_VARS="${ENV_VARS},SCREENSHOT_ENGINE_HOST=${SCREENSHOT_ENGINE_HOST}"
fi

echo "[1/4] Setting project..."
gcloud config set project "${PROJECT_ID}"

echo "[2/4] Building container image..."
gcloud builds submit \
  --tag "${IMAGE}:latest" \
  --timeout=900s \
  -f deploy/Dockerfile.cloudrun .

echo "[3/4] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}:latest" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --set-env-vars "${ENV_VARS}" \
  --set-secrets "GEMINI_API_KEY=telos-gemini-api-key:latest,TELOS_API_TOKEN=telos-api-token:latest" \
  --cpu 2 \
  --memory 1Gi \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 3

echo "[4/4] Service URL..."
gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format "value(status.url)"
