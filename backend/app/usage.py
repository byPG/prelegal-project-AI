import threading
from datetime import date

from .config import settings


class DailyLimitExceededError(Exception):
    """Raised when the OpenRouter free-tier daily request budget is exhausted."""


class _DailyRequestCounter:
    """In-memory counter of LLM calls made today.

    Not shared across processes/workers and resets whenever the process
    restarts — acceptable here since the app runs as a single uvicorn
    process and the whole point is a soft local guard against blowing
    through OpenRouter's free-tier daily cap, not an authoritative ledger.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._day: date | None = None
        self._count = 0

    def record_and_check(self) -> None:
        """Record one request; raise if today's budget is already spent.

        Called before making the LLM call, so a rejected request never
        costs any quota.
        """
        with self._lock:
            today = date.today()
            if today != self._day:
                self._day = today
                self._count = 0

            if self._count >= settings.openrouter_daily_request_limit:
                raise DailyLimitExceededError(
                    f"Daily limit of {settings.openrouter_daily_request_limit} AI requests reached. "
                    "Please try again tomorrow."
                )

            self._count += 1

    def reset(self) -> None:
        """Test-only hook to clear accumulated state between test cases."""
        with self._lock:
            self._day = None
            self._count = 0


daily_request_counter = _DailyRequestCounter()
