import pytest

from app.config import settings
from app.llm import complete_structured
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


def test_complete_structured_returns_primary_result_on_success(monkeypatch):
    def fake_completion(**kwargs):
        assert kwargs["model"] == settings.openrouter_primary_model
        return _FakeResponse('{"reply": "hi", "field_updates": {}}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)
    assert result.reply == "hi"


def test_complete_structured_tolerates_a_markdown_code_fence(monkeypatch):
    def fake_completion(**kwargs):
        return _FakeResponse('```json\n{"reply": "hi", "field_updates": {}}\n```')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)
    assert result.reply == "hi"


def test_complete_structured_falls_back_when_primary_fails(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs["model"])
        if kwargs["model"] == settings.openrouter_primary_model:
            raise RuntimeError("primary is down")
        return _FakeResponse('{"reply": "from fallback", "field_updates": {}}')

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    result = complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)

    assert result.reply == "from fallback"
    assert calls == [settings.openrouter_primary_model, settings.openrouter_fallback_model]


def test_complete_structured_refuses_a_fallback_attempt_that_would_exceed_the_budget(monkeypatch):
    # Simulate the router's pre-check having already spent the day's only
    # unit of budget on the (about-to-fail) primary attempt.
    monkeypatch.setattr(settings, "openrouter_daily_request_limit", 1)
    daily_request_counter.record_and_check()

    def fake_completion(**kwargs):
        raise RuntimeError("primary is down")

    monkeypatch.setattr("app.llm.litellm.completion", fake_completion)

    # The fallback would be a second real OpenRouter request — with no
    # budget left, it must never be attempted.
    with pytest.raises(DailyLimitExceededError):
        complete_structured([{"role": "user", "content": "hi"}], ChatTurnReply)
