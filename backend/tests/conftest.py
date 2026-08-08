import pytest
from fastapi.testclient import TestClient

from app.config import settings


@pytest.fixture(autouse=True)
def _reset_daily_usage_counter():
    from app.usage import daily_request_counter

    daily_request_counter.reset()
    yield


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "test.sqlite3"))

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
