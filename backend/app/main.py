import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import BACKEND_DIR, INSECURE_DEFAULT_JWT_SECRET, settings
from .database import reset_database
from .routers import auth, chat

STATIC_DIR = BACKEND_DIR / "static"

logger = logging.getLogger("prelegal")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.jwt_secret == INSECURE_DEFAULT_JWT_SECRET:
        logger.warning(
            "JWT_SECRET is unset and falling back to the well-known default "
            "committed in .env.example — tokens can be forged by anyone with "
            "repo access. Set a real JWT_SECRET before running outside local dev."
        )
    reset_database()
    yield


app = FastAPI(title="Prelegal API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# The Next.js static export (see frontend/next.config.ts) is copied into
# backend/static at Docker build time and served directly from here, so the
# whole app is a single process on a single port. In local development
# without that export present, only the /api/* routes are available.
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
