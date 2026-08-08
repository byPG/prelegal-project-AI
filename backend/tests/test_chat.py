from app.config import settings
from app.llm import LlmUnavailableError
from app.mutual_nda import GREETING
from app.schemas import ChatTurnReply, MutualNdaFields


def test_greeting_is_hardcoded_and_never_calls_the_model(client, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("greeting must not call the model")

    monkeypatch.setattr("app.routers.chat.complete_structured", fail_if_called)

    response = client.get("/api/chat/greeting")

    assert response.status_code == 200
    assert response.json() == {"reply": GREETING}


def test_send_message_returns_only_the_models_field_updates(client, monkeypatch):
    # The response is deliberately sparse (only what the model actually
    # learned this turn) — merging that with whatever the client already
    # knows is the frontend's job, done against its *current* state, not
    # something the backend bakes in against a possibly-stale request
    # snapshot. See routers/chat.py for why.
    def fake_complete(messages, response_model):
        return ChatTurnReply(
            reply="Got it, thanks.",
            field_updates=MutualNdaFields(partyOneName="Acme, Inc."),
        )

    monkeypatch.setattr("app.routers.chat.complete_structured", fake_complete)

    response = client.post(
        "/api/chat/message",
        json={
            "messages": [{"role": "user", "content": "We're Acme, Inc."}],
            "fields": {"partyTwoName": "Beta Labs LLC"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Got it, thanks."
    assert body["fields"]["partyOneName"] == "Acme, Inc."
    # Not echoed back — the model made no claim about this field this turn.
    assert body["fields"]["partyTwoName"] is None


def test_send_message_leaves_untouched_fields_as_none(client, monkeypatch):
    def fake_complete(messages, response_model):
        # Model has no new info this turn — every field_update stays None.
        return ChatTurnReply(reply="Could you tell me the purpose of the NDA?")

    monkeypatch.setattr("app.routers.chat.complete_structured", fake_complete)

    response = client.post(
        "/api/chat/message",
        json={
            "messages": [{"role": "user", "content": "Not sure yet"}],
            "fields": {"partyOneName": "Acme, Inc."},
        },
    )

    assert response.status_code == 200
    assert all(value is None for value in response.json()["fields"].values())


def test_send_message_requires_at_least_one_message(client):
    response = client.post("/api/chat/message", json={"messages": [], "fields": {}})
    assert response.status_code == 422


def test_send_message_maps_llm_failure_to_503(client, monkeypatch):
    def always_fails(messages, response_model):
        raise LlmUnavailableError("both models failed")

    monkeypatch.setattr("app.routers.chat.complete_structured", always_fails)

    response = client.post(
        "/api/chat/message",
        json={"messages": [{"role": "user", "content": "hi"}], "fields": {}},
    )

    assert response.status_code == 503


def test_send_message_enforces_daily_limit_before_calling_the_model(client, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_daily_request_limit", 1)

    calls = []

    def fake_complete(messages, response_model):
        calls.append(1)
        return ChatTurnReply(reply="ok")

    monkeypatch.setattr("app.routers.chat.complete_structured", fake_complete)

    payload = {"messages": [{"role": "user", "content": "hi"}], "fields": {}}
    first = client.post("/api/chat/message", json=payload)
    second = client.post("/api/chat/message", json=payload)

    assert first.status_code == 200
    assert second.status_code == 429
    assert len(calls) == 1  # the rejected request never reached the model
