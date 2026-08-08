# Prelegal backend

FastAPI service, managed as a [uv](https://docs.astral.sh/uv/) project. This is the V1
technical foundation: SQLite-backed signup/signin (JWT) and, once the frontend static
export exists at `backend/static`, serving of the whole app on one port.

## Local development

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

The server reads `OPENROUTER_API_KEY` and other settings from the repo-root `.env`
(see `.env.example`). A backend-local `.env` may be added to override individual
values for local development; it is gitignored.

## Tests

```bash
cd backend
uv run pytest
```

## Database

SQLite at `backend/data/prelegal.sqlite3` by default (override with `DATABASE_PATH`).
The `users` table is dropped and recreated on every app startup — this is a temporary
store for the V1 foundation, not meant to persist across restarts.

## Endpoints

- `GET /api/health` — liveness check
- `POST /api/auth/signup` — `{ "email": str, "password": str (>=8 chars) }` → `201` with the created user
- `POST /api/auth/signin` — `{ "email": str, "password": str }` → `200` with a bearer JWT
