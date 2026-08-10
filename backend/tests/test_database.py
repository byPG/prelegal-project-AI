from app.config import settings
from app.database import get_connection, init_database


def test_init_database_creates_empty_tables(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "init.sqlite3"))

    init_database()

    with get_connection() as conn:
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        document_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    assert user_count == 0
    assert document_count == 0


def test_init_database_preserves_existing_rows_on_repeated_calls(tmp_path, monkeypatch):
    # Regression check: init_database() runs on every container start, so it
    # must be idempotent rather than wiping data — the whole point of PREL-7
    # persistence is that a restart doesn't discard users/documents.
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "init.sqlite3"))
    init_database()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            ("a@example.com", "hash"),
        )

    init_database()

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert count == 1


def test_deleting_a_user_cascades_to_their_documents(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "cascade.sqlite3"))
    init_database()

    with get_connection() as conn:
        user_id = conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            ("a@example.com", "hash"),
        ).lastrowid
        conn.execute(
            "INSERT INTO documents (user_id, document_type_id, title, fields_json) VALUES (?, ?, ?, ?)",
            (user_id, "mutual-nda", "Untitled", "{}"),
        )

    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    assert count == 0
