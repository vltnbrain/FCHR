#!/usr/bin/env bash
set -euo pipefail

PROJECT="${PROJECT:-}"
REGION="${REGION:-}"
SERVICE_NAME="${SERVICE_NAME:-aihub-backend}"
REPO_NAME="${REPO_NAME:-aihub}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ENV_FILE="${ENV_FILE:-ai-hub/infra/cloudrun.env.example.yaml}"
ALLOW_UNAUTH="${ALLOW_UNAUTH:-false}"

usage() {
  echo "Usage: PROJECT=... REGION=... [SERVICE_NAME=aihub-backend] [REPO_NAME=aihub] [IMAGE_TAG=latest] [ENV_FILE=ai-hub/infra/cloudrun.env.example.yaml] [ALLOW_UNAUTH=true] $0" >&2
}

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI not found. Install Google Cloud SDK." >&2
  exit 1
fi

if [[ -z "$PROJECT" || -z "$REGION" ]]; then
  usage; exit 1
fi

gcloud config set project "$PROJECT" >/dev/null
gcloud config set run/region "$REGION" >/dev/null

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT}/${REPO_NAME}/${SERVICE_NAME}:${IMAGE_TAG}"

echo "Ensuring Artifact Registry repo '${REPO_NAME}' exists in ${REGION}..."
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO_NAME" --repository-format=docker --location="$REGION" --description="AI Hub containers"
fi

echo "Building image with Cloud Build: ${IMAGE_URI}"
gcloud builds submit "ai-hub/backend" --tag "$IMAGE_URI"

echo "Deploying to Cloud Run service '${SERVICE_NAME}' in ${REGION}..."
ARGS=(run deploy "$SERVICE_NAME" --image "$IMAGE_URI" --region "$REGION" --platform managed --port 8080)
if [[ "$ALLOW_UNAUTH" == "true" ]]; then ARGS+=(--allow-unauthenticated); fi
if [[ -f "$ENV_FILE" ]]; then ARGS+=(--env-vars-file "$ENV_FILE"); fi

gcloud "${ARGS[@]}"

URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')
echo "Deployed successfully: $URL"
echo "Note: Ensure DATABASE_URI points to Cloud SQL/Postgres and Redis/worker needs separate setup if used."

