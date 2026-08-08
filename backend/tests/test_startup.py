import logging

from fastapi.testclient import TestClient

from app.config import INSECURE_DEFAULT_JWT_SECRET, settings


def test_startup_warns_when_jwt_secret_is_the_committed_default(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "warn.sqlite3"))
    monkeypatch.setattr(settings, "jwt_secret", INSECURE_DEFAULT_JWT_SECRET)

    from app.main import app

    with caplog.at_level(logging.WARNING, logger="prelegal"):
        with TestClient(app):
            pass

    assert any("JWT_SECRET" in record.getMessage() for record in caplog.records)


def test_startup_is_silent_when_jwt_secret_is_overridden(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "no_warn.sqlite3"))
    monkeypatch.setattr(settings, "jwt_secret", "a-real-per-deployment-secret")

    from app.main import app

    with caplog.at_level(logging.WARNING, logger="prelegal"):
        with TestClient(app):
            pass

    assert not any("JWT_SECRET" in record.getMessage() for record in caplog.records)
