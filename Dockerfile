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

# templates/*.md + catalog.json are parsed by app/templates.py at import
# time (REPO_ROOT resolves to /app here, one level up from /app/backend),
# so they need to land at /app/templates and /app/catalog.json — not just
# committed to git — or the app crashes on startup with a FileNotFoundError.
COPY templates/ /app/templates/
COPY catalog.json /app/catalog.json

RUN uv sync --frozen --no-dev

ENV PATH="/app/backend/.venv/bin:$PATH"
EXPOSE 8000

# The SQLite file lives here (see config.py's database_path); declaring it
# as a volume documents that this path is meant to be mounted (see
# scripts/start-*) so data survives `docker rm -f` + a fresh `docker run`,
# not just an in-place restart of the same container.
VOLUME ["/app/backend/data"]

# Invoke uvicorn directly rather than via `uv run`: `uv run` re-checks (and,
# if it thinks anything drifted, re-syncs over the network) the environment
# on every invocation, which turns container startup into something that
# can silently hit the network and install packages instead of just running
# the image that was already frozen-built.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
