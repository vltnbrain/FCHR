#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=${REPO_DIR:-$HOME/FCHR}
cd "$REPO_DIR"

echo "Pulling latest..."
git pull --ff-only || true

echo "Ensuring .env exists..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
fi

echo "Bringing up stack..."
docker compose -f infra/prod/docker-compose.yml up -d --build

echo "Done. Health:"
curl -sf http://localhost/healthz && echo || echo "healthz failed"

