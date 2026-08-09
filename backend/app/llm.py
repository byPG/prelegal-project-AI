import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

import litellm
from pydantic import BaseModel

from .config import settings
from .usage import daily_request_counter

logger = logging.getLogger("prelegal")

ModelT = TypeVar("ModelT", bound=BaseModel)

_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

_MAX_ATTEMPTS = 2

# litellm's own `timeout=` kwarg turned out not to reliably bound the call
# for every model/provider OpenRouter's adaptive router can pick — verified
# live: a request hung 100+ seconds with `timeout=45` set and never even
# raised. Running the call in its own thread and giving up on *that*
# (rather than trusting the call to give up on itself) is a hard guarantee
# regardless of what litellm/httpx does internally. The abandoned thread
# may keep running in the background until it eventually finishes on its
# own — Python has no safe way to kill a thread — but the request handler
# is no longer hostage to it.
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="llm-call")


class LlmUnavailableError(Exception):
    """Raised when every attempt fails to produce a usable response."""


def _strip_code_fence(content: str) -> str:
    # Smaller/free-tier models sometimes wrap structured-output JSON in a
    # markdown code fence even when told not to — tolerate that rather
    # than treating it as a hard failure.
    return _CODE_FENCE.sub("", content.strip())


def complete_structured(messages: list[dict[str, str]], response_model: type[ModelT]) -> ModelT:
    """Call settings.openrouter_model and parse its reply into `response_model`.

    Retries once on any failure (rate limit, timeout, the picked-for-this-
    request free model going down, ...) rather than looping — a clear
    failure beats silently burning quota. Since the model is OpenRouter's
    own adaptive free-model router (see config.py), a retry can genuinely
    land on a different underlying model, not just repeat the same
    failure — this isn't a "primary vs. fallback" split any more.

    The caller accounts for the first attempt via daily_request_counter
    before calling this function. The retry is itself a second real
    OpenRouter request, so it's counted here, right before it's made —
    otherwise the local usage guard would silently undercount real usage
    by up to 2x whenever the first attempt fails. If the budget is already
    spent, this raises DailyLimitExceededError instead of retrying.
    """
    last_error: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        if attempt > 0:
            daily_request_counter.record_and_check()
        try:
            future = _executor.submit(
                litellm.completion,
                model=settings.openrouter_model,
                messages=messages,
                api_key=settings.openrouter_api_key,
                response_format=response_model,
                timeout=settings.openrouter_request_timeout_seconds,
            )
            # future.result()'s timeout is the enforcement that actually
            # works; the timeout= kwarg above is kept as a best-effort hint
            # to litellm/httpx, not relied on alone.
            response = future.result(timeout=settings.openrouter_request_timeout_seconds)
            content = response.choices[0].message.content
            return response_model.model_validate_json(_strip_code_fence(content))
        except Exception as exc:
            # Includes concurrent.futures.TimeoutError (a subclass of the
            # builtin TimeoutError -> OSError -> Exception), raised by
            # future.result() above when the call didn't finish in time.
            last_error = exc
            logger.warning(
                "LLM call failed (attempt %d/%d) for model %s",
                attempt + 1,
                _MAX_ATTEMPTS,
                settings.openrouter_model,
                exc_info=True,
            )

    raise LlmUnavailableError(
        f"{settings.openrouter_model} failed after {_MAX_ATTEMPTS} attempts"
    ) from last_error
