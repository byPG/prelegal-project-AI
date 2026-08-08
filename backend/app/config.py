from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

INSECURE_DEFAULT_JWT_SECRET = "dev-insecure-secret-change-me"


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env files.

    The repo-root `.env` (documented in CLAUDE.md) is read first so secrets like
    OPENROUTER_API_KEY are picked up; a backend-local `.env` (if present) can
    override individual values for local development.
    """

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_path: str = str(BACKEND_DIR / "data" / "prelegal.sqlite3")

    jwt_secret: str = INSECURE_DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    openrouter_api_key: str | None = None


settings = Settings()
