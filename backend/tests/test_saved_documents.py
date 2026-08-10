import pytest


@pytest.fixture()
def auth_headers(client):
    client.post("/api/auth/signup", json={"email": "owner@example.com", "password": "supersecret"})
    signin = client.post(
        "/api/auth/signin", json={"email": "owner@example.com", "password": "supersecret"}
    )
    token = signin.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def other_auth_headers(client):
    client.post("/api/auth/signup", json={"email": "other@example.com", "password": "supersecret"})
    signin = client.post(
        "/api/auth/signin", json={"email": "other@example.com", "password": "supersecret"}
    )
    token = signin.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _save_payload(**overrides):
    payload = {
        "document_type_id": "mutual-nda",
        "title": "Acme x Widgets NDA",
        "fields": {"partyOneName": "Acme"},
    }
    payload.update(overrides)
    return payload


def test_save_document_requires_auth(client):
    response = client.post("/api/saved-documents", json=_save_payload())
    assert response.status_code == 401


def test_save_document_creates_and_returns_it(client, auth_headers):
    response = client.post("/api/saved-documents", json=_save_payload(), headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["document_type_id"] == "mutual-nda"
    assert body["document_name"] == "Mutual Non-Disclosure Agreement"
    assert body["title"] == "Acme x Widgets NDA"
    assert body["fields"] == {"partyOneName": "Acme"}


def test_save_document_rejects_unknown_document_type(client, auth_headers):
    response = client.post(
        "/api/saved-documents", json=_save_payload(document_type_id="not-a-real-type"), headers=auth_headers
    )
    assert response.status_code == 422


def test_list_saved_documents_only_returns_the_caller_own(client, auth_headers, other_auth_headers):
    client.post("/api/saved-documents", json=_save_payload(), headers=auth_headers)
    client.post("/api/saved-documents", json=_save_payload(title="Someone else's"), headers=other_auth_headers)

    response = client.get("/api/saved-documents", headers=auth_headers)

    assert response.status_code == 200
    titles = [doc["title"] for doc in response.json()]
    assert titles == ["Acme x Widgets NDA"]


def test_list_saved_documents_orders_newest_updated_first(client, auth_headers):
    first = client.post("/api/saved-documents", json=_save_payload(title="First"), headers=auth_headers).json()
    client.post("/api/saved-documents", json=_save_payload(title="Second"), headers=auth_headers)

    client.put(
        f"/api/saved-documents/{first['id']}",
        json={"title": "First (updated)", "fields": {}},
        headers=auth_headers,
    )

    response = client.get("/api/saved-documents", headers=auth_headers)
    titles = [doc["title"] for doc in response.json()]
    assert titles == ["First (updated)", "Second"]


def test_get_saved_document_returns_404_for_another_users_document(client, auth_headers, other_auth_headers):
    created = client.post("/api/saved-documents", json=_save_payload(), headers=auth_headers).json()

    response = client.get(f"/api/saved-documents/{created['id']}", headers=other_auth_headers)

    assert response.status_code == 404


def test_update_saved_document_changes_title_and_fields(client, auth_headers):
    created = client.post("/api/saved-documents", json=_save_payload(), headers=auth_headers).json()

    response = client.put(
        f"/api/saved-documents/{created['id']}",
        json={"title": "Renamed", "fields": {"partyOneName": "Updated Co"}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed"
    assert body["fields"] == {"partyOneName": "Updated Co"}
    assert body["id"] == created["id"]


def test_update_saved_document_returns_404_for_another_users_document(client, auth_headers, other_auth_headers):
    created = client.post("/api/saved-documents", json=_save_payload(), headers=auth_headers).json()

    response = client.put(
        f"/api/saved-documents/{created['id']}",
        json={"title": "Hijacked", "fields": {}},
        headers=other_auth_headers,
    )

    assert response.status_code == 404


def test_delete_saved_document_removes_it(client, auth_headers):
    created = client.post("/api/saved-documents", json=_save_payload(), headers=auth_headers).json()

    delete_response = client.delete(f"/api/saved-documents/{created['id']}", headers=auth_headers)
    get_response = client.get(f"/api/saved-documents/{created['id']}", headers=auth_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_saved_document_returns_404_for_another_users_document(client, auth_headers, other_auth_headers):
    created = client.post("/api/saved-documents", json=_save_payload(), headers=auth_headers).json()

    response = client.delete(f"/api/saved-documents/{created['id']}", headers=other_auth_headers)

    assert response.status_code == 404
