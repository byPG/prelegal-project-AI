# syntax=docker/dockerfile:1

# ---- Frontend: build the Next.js static export ----
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---- Backend: install deps with uv, serve the app ----
FROM python:3.12-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY backend/ .
COPY --from=frontend-build /app/frontend/out ./static

RUN uv sync --frozen --no-dev

ENV PATH="/app/backend/.venv/bin:$PATH"
EXPOSE 8000

# Invoke uvicorn directly rather than via `uv run`: `uv run` re-checks (and,
# if it thinks anything drifted, re-syncs over the network) the environment
# on every invocation, which turns container startup into something that
# can silently hit the network and install packages instead of just running
# the image that was already frozen-built.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
