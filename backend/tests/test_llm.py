import pytest

from app.config import settings
from app.llm import LlmUnavailableError, complete_structured
from app.schemas import ChatTurnReply
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


def test_complete_structured_returns_result_on_success(monkeypatch):
    def fake_completion(**kwargs):
        assert kwargs["model"] == settings.openrouter_model
        return _FakeResponse('{"reply": "hi", "field_updates": {}}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)
    assert result.reply == "hi"


def test_complete_structured_passes_a_request_timeout(monkeypatch):
    # Regression check: litellm.completion() with no timeout can hang
    # indefinitely if a provider accepts the connection but never replies
    # (observed for real — a request hung for 10+ minutes with no error).
    def fake_completion(**kwargs):
        assert kwargs["timeout"] == settings.openrouter_request_timeout_seconds
        return _FakeResponse('{"reply": "hi", "field_updates": {}}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)


def test_complete_structured_tolerates_a_markdown_code_fence(monkeypatch):
    def fake_completion(**kwargs):
        return _FakeResponse('```json\n{"reply": "hi", "field_updates": {}}\n```')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)
    assert result.reply == "hi"


def test_complete_structured_retries_once_after_a_failure(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs["model"])
        if len(calls) == 1:
            raise RuntimeError("transient failure")
        return _FakeResponse('{"reply": "second try worked", "field_updates": {}}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)

    assert result.reply == "second try worked"
    assert calls == [settings.openrouter_model, settings.openrouter_model]


def test_complete_structured_raises_llm_unavailable_after_exhausting_retries(monkeypatch):
    def always_fails(**kwargs):
        raise RuntimeError("still down")

    monkeypatch.setattr("app.llm.litellm.completion", always_fails)

    with pytest.raises(LlmUnavailableError):
        complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)


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
        complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)
