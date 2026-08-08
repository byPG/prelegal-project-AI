def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_signup_creates_user(client):
    response = client.post(
        "/api/auth/signup", json={"email": "person@example.com", "password": "supersecret"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "person@example.com"
    assert isinstance(body["id"], int)


def test_signup_rejects_duplicate_email(client):
    # Regression check: signup relies on the DB's UNIQUE constraint (via
    # sqlite3.IntegrityError) rather than a SELECT-then-INSERT check, so a
    # duplicate always surfaces as 409, not an unhandled 500.
    payload = {"email": "dup@example.com", "password": "supersecret"}
    first = client.post("/api/auth/signup", json=payload)
    second = client.post("/api/auth/signup", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Email is already registered"


def test_signup_rejects_short_password(client):
    response = client.post(
        "/api/auth/signup", json={"email": "short@example.com", "password": "abc123"}
    )
    assert response.status_code == 422


def test_signup_rejects_invalid_email(client):
    response = client.post(
        "/api/auth/signup", json={"email": "not-an-email", "password": "supersecret"}
    )
    assert response.status_code == 422


def test_signup_rejects_password_over_72_bytes(client):
    # 40 chars of "é" (2 bytes each in UTF-8) = 80 bytes, well past bcrypt's
    # 72-byte limit, but would slip past a naive character-count check.
    oversized_password = "é" * 40
    response = client.post(
        "/api/auth/signup", json={"email": "longpw@example.com", "password": oversized_password}
    )
    assert response.status_code == 422


def test_signin_returns_bearer_token(client):
    client.post(
        "/api/auth/signup", json={"email": "signin@example.com", "password": "supersecret"}
    )

    response = client.post(
        "/api/auth/signin", json={"email": "signin@example.com", "password": "supersecret"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_signin_rejects_wrong_password(client):
    client.post(
        "/api/auth/signup", json={"email": "wrongpw@example.com", "password": "supersecret"}
    )

    response = client.post(
        "/api/auth/signin", json={"email": "wrongpw@example.com", "password": "totallywrong"}
    )

    assert response.status_code == 401


def test_signin_rejects_unknown_email(client):
    response = client.post(
        "/api/auth/signin", json={"email": "nobody@example.com", "password": "supersecret"}
    )
    assert response.status_code == 401
