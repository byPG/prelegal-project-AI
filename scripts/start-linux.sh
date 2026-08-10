#!/usr/bin/env bash
# Build and start the Prelegal app container (Linux).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE_NAME="prelegal-app"
CONTAINER_NAME="prelegal-app"
# 8010, not 8000: keeps this container from colliding with other local
# projects that commonly default to 8000 (or 3000 for a Node dev server).
PORT="8010"

cd "$REPO_ROOT"

if [ ! -f .env ]; then
  echo "Warning: .env not found at repo root. Copy .env.example to .env and fill in secrets before starting." >&2
fi

echo "Building Docker image ($IMAGE_NAME)..."
docker build -t "$IMAGE_NAME" .

if [ "$(docker ps -aq -f "name=^${CONTAINER_NAME}\$")" ]; then
  echo "Removing existing container ($CONTAINER_NAME)..."
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

echo "Starting container ($CONTAINER_NAME) on port $PORT..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --env-file .env \
  -p "${PORT}:8000" \
  -v prelegal-data:/app/backend/data \
  "$IMAGE_NAME" >/dev/null

echo "Prelegal backend available at http://localhost:${PORT}"
