from app.config import settings
from app.documents import GREETING
from app.llm import LlmUnavailableError


def test_greeting_is_hardcoded_and_never_calls_the_model(client, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("greeting must not call the model")

    monkeypatch.setattr("app.routers.chat.complete_structured", fail_if_called)

    response = client.get("/api/chat/greeting")

    assert response.status_code == 200
    assert response.json() == {"reply": GREETING}


def test_send_message_without_a_document_lets_the_model_establish_one(client, monkeypatch):
    def fake_complete(messages, response_model):
        return response_model(reply="Let's set up a Mutual NDA.", document_id="mutual-nda")

    monkeypatch.setattr("app.routers.chat.complete_structured", fake_complete)

    response = client.post(
        "/api/chat/message",
        json={"messages": [{"role": "user", "content": "I need an NDA with a vendor"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "mutual-nda"
    # No fields extracted yet — the model wasn't given any field schema
    # to work with until a document type exists.
    assert body["fields"] == {}


def test_send_message_extracts_fields_once_a_document_is_established(client, monkeypatch):
    def fake_complete(messages, response_model):
        return response_model(reply="Got it, thanks.", field_updates={"partyOneName": "Acme, Inc."})

    monkeypatch.setattr("app.routers.chat.complete_structured", fake_complete)

    response = client.post(
        "/api/chat/message",
        json={
            "messages": [{"role": "user", "content": "We're Acme, Inc."}],
            "document_id": "mutual-nda",
            "fields": {"partyTwoName": "Beta Labs LLC"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "mutual-nda"
    assert body["fields"]["partyOneName"] == "Acme, Inc."
    # Not echoed back — the model made no claim about this field this turn.
    assert body["fields"]["partyTwoName"] is None


def test_document_id_stays_sticky_when_the_model_does_not_change_it(client, monkeypatch):
    def fake_complete(messages, response_model):
        return response_model(reply="Could you tell me the purpose of the agreement?")

    monkeypatch.setattr("app.routers.chat.complete_structured", fake_complete)

    response = client.post(
        "/api/chat/message",
        json={
            "messages": [{"role": "user", "content": "Not sure yet"}],
            "document_id": "mutual-nda",
            "fields": {"partyOneName": "Acme, Inc."},
        },
    )

    assert response.status_code == 200
    assert response.json()["document_id"] == "mutual-nda"


def test_send_message_requires_at_least_one_message(client):
    response = client.post("/api/chat/message", json={"messages": []})
    assert response.status_code == 422


def test_send_message_maps_llm_failure_to_503(client, monkeypatch):
    def always_fails(messages, response_model):
        raise LlmUnavailableError("model failed after retries")

    monkeypatch.setattr("app.routers.chat.complete_structured", always_fails)

    response = client.post(
        "/api/chat/message",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 503


def test_send_message_enforces_daily_limit_before_calling_the_model(client, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_daily_request_limit", 1)

    calls = []

    def fake_complete(messages, response_model):
        calls.append(1)
        return response_model(reply="ok")

    monkeypatch.setattr("app.routers.chat.complete_structured", fake_complete)

    payload = {"messages": [{"role": "user", "content": "hi"}]}
    first = client.post("/api/chat/message", json=payload)
    second = client.post("/api/chat/message", json=payload)

    assert first.status_code == 200
    assert second.status_code == 429
    assert len(calls) == 1  # the rejected request never reached the model
