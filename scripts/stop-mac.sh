#!/usr/bin/env bash
# Stop and remove the Prelegal app container (macOS).
set -euo pipefail

CONTAINER_NAME="prelegal-app"

if [ "$(docker ps -aq -f "name=^${CONTAINER_NAME}\$")" ]; then
  echo "Stopping and removing container ($CONTAINER_NAME)..."
  docker rm -f "$CONTAINER_NAME" >/dev/null
  echo "Stopped."
else
  echo "Container ($CONTAINER_NAME) is not running."
fi
