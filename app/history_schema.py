import sqlite3
from contextlib import closing

from app import storage
from app.history_ids import new_public_id


def init_history_store() -> None:
    storage.ensure_storage_dirs()
    with closing(storage.connect()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                restaurant TEXT NOT NULL,
                source_label TEXT NOT NULL,
                source_url TEXT,
                file_name TEXT,
                mime_type TEXT,
                file_path TEXT,
                menu_json TEXT,
                recipe_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        ensure_column(conn, "history", "owner_user_id", "INTEGER")
        ensure_column(conn, "history", "public_id", "TEXT")
        ensure_column(conn, "history", "stored_bytes", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "history", "deleted_at", "TEXT")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_history_public_id ON history(public_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_owner_active ON history(owner_user_id, deleted_at)"
        )
        conn.commit()


def ensure_column(
    conn: sqlite3.Connection, table_name: str, column_name: str, definition: str
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def backfill_public_ids(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id FROM history WHERE public_id IS NULL OR public_id = ''"
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE history SET public_id = ? WHERE id = ?",
            (new_public_id(), row["id"]),
        )
