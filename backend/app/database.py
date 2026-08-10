import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_type_id TEXT NOT NULL,
    title TEXT NOT NULL,
    fields_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents (user_id);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection, committing on success and always closing it.

    Plain `with sqlite3.connect(...) as conn:` only wraps the transaction
    (commit/rollback) — it does not close the connection — so callers must
    go through this helper instead of connecting directly.
    """
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """Create the SQLite file and tables if they don't already exist.

    Deliberately non-destructive: the SQLite file lives on a Docker volume
    (see the Dockerfile) so signed-up users and their saved documents
    survive container restarts/redeploys. Every statement in SCHEMA is
    `CREATE ... IF NOT EXISTS`, so calling this on an already-initialized
    database is a no-op rather than a wipe.
    """
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.executescript(SCHEMA)
