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
    # OpenRouter's own "Free Models Router" — picks whichever free model is
    # currently live and capable of the request (structured output, tool
    # calling, ...), rather than a specific pinned `:free` slug. Pinning one
    # (e.g. openai/gpt-oss-120b:free) was tried and rotted away within
    # hours as OpenRouter pulled/repriced it, exactly the volatility
    # CLAUDE.md's AI-layer section warns about — the adaptive router is
    # self-healing against that instead of needing to be re-pinned by hand.
    #
    # Note the doubled "openrouter/": litellm's own "openrouter/" custom-
    # provider prefix is stripped before the remainder is sent to
    # OpenRouter's API, so the *actual* OpenRouter model id here —
    # "openrouter/free" — has to be given as "openrouter/openrouter/free"
    # or litellm sends the single word "free", which OpenRouter doesn't
    # recognize as any model at all.
    openrouter_model: str = "openrouter/openrouter/free"
    openrouter_daily_request_limit: int = 200
    # Without an explicit timeout, litellm/httpx will wait indefinitely if
    # a provider accepts the connection but never responds (seen for real:
    # a request hung for 10+ minutes with no error and no reply). A hang
    # is worse than a clean failure — it burns the retry's usefulness and
    # leaves the user staring at a spinner forever instead of getting a
    # clear error to act on.
    openrouter_request_timeout_seconds: float = 45.0


settings = Settings()
