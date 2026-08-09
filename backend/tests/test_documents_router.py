def test_list_documents_returns_all_eleven(client):
    response = client.get("/api/documents")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 11
    assert {"id", "name", "description"} <= body[0].keys()
    assert "fields" not in body[0]  # summary endpoint, not the full parsed template


def test_get_document_detail_returns_fields_and_body(client):
    response = client.get("/api/documents/mutual-nda")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "mutual-nda"
    field_keys = {field["key"] for field in body["fields"]}
    assert "purpose" in field_keys
    assert "partyOneName" in field_keys
    assert len(body["body"]) > 0


def test_get_document_detail_404s_for_unknown_id(client):
    response = client.get("/api/documents/not-a-real-document")
    assert response.status_code == 404
