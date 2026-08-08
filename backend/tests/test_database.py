from app.config import settings
from app.database import get_connection, reset_database


def test_reset_database_creates_empty_users_table(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "reset.sqlite3"))

    reset_database()

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert count == 0


def test_reset_database_wipes_existing_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "reset.sqlite3"))
    reset_database()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            ("a@example.com", "hash"),
        )
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert count == 1

    reset_database()

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert count == 0
