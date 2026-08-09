import time

import pytest
from pydantic import BaseModel

from app.config import settings
from app.llm import LlmUnavailableError, complete_structured
from app.usage import DailyLimitExceededError, daily_request_counter


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class _MinimalReply(BaseModel):
    """A stand-in structured-output shape — complete_structured() is generic
    over any Pydantic model, so these tests don't need to depend on the
    real (and, since PREL-6, per-request dynamically built) chat schema."""

    reply: str


def test_complete_structured_returns_result_on_success(monkeypatch):
    def fake_completion(**kwargs):
        assert kwargs["model"] == settings.openrouter_model
        return _FakeResponse('{"reply": "hi"}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], _MinimalReply)
    assert result.reply == "hi"


def test_complete_structured_passes_a_request_timeout(monkeypatch):
    # Regression check: litellm.completion() with no timeout can hang
    # indefinitely if a provider accepts the connection but never replies
    # (observed for real — a request hung for 10+ minutes with no error).
    def fake_completion(**kwargs):
        assert kwargs["timeout"] == settings.openrouter_request_timeout_seconds
        return _FakeResponse('{"reply": "hi"}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    complete_structured([{"role": "user", "content": "hi"}], _MinimalReply)


def test_complete_structured_gives_up_on_a_call_that_ignores_its_own_timeout(monkeypatch):
    # Regression check for a real failure: litellm's own `timeout=` kwarg
    # did not reliably bound the call for every model OpenRouter's adaptive
    # router could pick — verified live, a request hung 100+ seconds with
    # timeout=45 set and never even raised. complete_structured must not
    # trust the callee to give up on itself; it has to enforce the bound
    # from the outside (see the ThreadPoolExecutor in app/llm.py) so a
    # call that blocks forever, ignoring its own timeout kwarg entirely,
    # still returns control to the caller.
    monkeypatch.setattr(settings, "openrouter_request_timeout_seconds", 0.2)

    def fake_completion_that_ignores_its_timeout(**kwargs):
        time.sleep(2)  # much longer than the 0.2s budget above
        return _FakeResponse('{"reply": "too late"}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion_that_ignores_its_timeout)

    started = time.monotonic()
    with pytest.raises(LlmUnavailableError):
        complete_structured([{"role": "user", "content": "hi"}], _MinimalReply)
    elapsed = time.monotonic() - started

    # Two attempts at ~0.2s each, plus scheduling overhead — nowhere near
    # the 2s+2s the fake call would take if its timeout were honored.
    assert elapsed < 1.5


def test_complete_structured_tolerates_a_markdown_code_fence(monkeypatch):
    def fake_completion(**kwargs):
        return _FakeResponse('```json\n{"reply": "hi"}\n```')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], _MinimalReply)
    assert result.reply == "hi"


def test_complete_structured_retries_once_after_a_failure(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs["model"])
        if len(calls) == 1:
            raise RuntimeError("transient failure")
        return _FakeResponse('{"reply": "second try worked"}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], _MinimalReply)

    assert result.reply == "second try worked"
    assert calls == [settings.openrouter_model, settings.openrouter_model]


def test_complete_structured_raises_llm_unavailable_after_exhausting_retries(monkeypatch):
    def always_fails(**kwargs):
        raise RuntimeError("still down")

    monkeypatch.setattr("app.llm.litellm.completion", always_fails)

    with pytest.raises(LlmUnavailableError):
        complete_structured([{"role": "user", "content": "hi"}], _MinimalReply)


def test_complete_structured_refuses_a_retry_that_would_exceed_the_budget(monkeypatch):
    # Simulate the router's pre-check having already spent the day's only
    # unit of budget on the (about-to-fail) first attempt.
    monkeypatch.setattr(settings, "openrouter_daily_request_limit", 1)
    daily_request_counter.record_and_check()

    def fake_completion(**kwargs):
        raise RuntimeError("first attempt is down")

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    # The retry would be a second real OpenRouter request — with no budget
    # left, it must never be attempted.
    with pytest.raises(DailyLimitExceededError):
        complete_structured([{"role": "user", "content": "hi"}], _MinimalReply)
