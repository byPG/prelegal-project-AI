import pytest
from fastapi.testclient import TestClient

from app.config import settings


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "test.sqlite3"))

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
