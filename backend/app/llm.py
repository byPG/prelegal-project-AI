import logging
import re
from typing import TypeVar

import litellm
from pydantic import BaseModel

from .config import settings
from .usage import daily_request_counter

logger = logging.getLogger("prelegal")

ModelT = TypeVar("ModelT", bound=BaseModel)

_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class LlmUnavailableError(Exception):
    """Raised when both the primary and fallback models fail to respond."""


def _strip_code_fence(content: str) -> str:
    # Smaller/free-tier models sometimes wrap structured-output JSON in a
    # markdown code fence even when told not to — tolerate that rather
    # than treating it as a hard failure.
    return _CODE_FENCE.sub("", content.strip())


def complete_structured(messages: list[dict[str, str]], response_model: type[ModelT]) -> ModelT:
    """Call the chat model and parse its reply into `response_model`.

    Tries the configured primary model first; on any failure (rate limit,
    timeout, provider outage, ...) retries once against the fallback model
    rather than looping — a clear failure beats silently burning quota.

    The caller accounts for the primary attempt via daily_request_counter
    before calling this function. Falling back to a second model is itself
    a second real OpenRouter request, so that attempt is counted here,
    right before it's made — otherwise the local usage guard would
    silently undercount real usage by up to 2x whenever the primary model
    is unavailable. If the budget is already spent, this raises
    DailyLimitExceededError instead of making the fallback call.
    """
    models = (settings.openrouter_primary_model, settings.openrouter_fallback_model)
    for index, model in enumerate(models):
        if index > 0:
            daily_request_counter.record_and_check()
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                api_key=settings.openrouter_api_key,
                response_format=response_model,
            )
            content = response.choices[0].message.content
            return response_model.model_validate_json(_strip_code_fence(content))
        except Exception:
            logger.warning("LLM call failed for model %s", model, exc_info=True)

    raise LlmUnavailableError(
        f"Both {settings.openrouter_primary_model} and {settings.openrouter_fallback_model} failed"
    )
