import os
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import storage
from app.history_repository import mark_history_deleted
from app.history_schema import init_history_store

DEFAULT_UPLOAD_RETENTION_DAYS = 30


def delete_history_record(owner_user_id: int, public_id: str) -> bool:
    file_path = mark_history_deleted(owner_user_id, public_id)
    if file_path is None:
        return False
    delete_stored_file(file_path)
    return True


def cleanup_expired_uploads(retention_days: int | None = None) -> int:
    init_history_store()
    days = get_upload_retention_days() if retention_days is None else retention_days
    if days <= 0:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted_at = datetime.now(timezone.utc).isoformat()
    with closing(storage.connect()) as conn:
        rows = conn.execute(
            """
            SELECT id, file_path
            FROM history
            WHERE file_path IS NOT NULL
              AND file_path != ''
              AND deleted_at IS NULL
              AND created_at < ?
            """,
            (cutoff.isoformat(),),
        ).fetchall()
        record_ids = [row["id"] for row in rows]
        if record_ids:
            conn.executemany(
                "UPDATE history SET deleted_at = ? WHERE id = ?",
                [(deleted_at, record_id) for record_id in record_ids],
            )
        conn.commit()

    for row in rows:
        delete_stored_file(row["file_path"])
    return len(rows)


def stored_upload_path(record_name: str) -> Path:
    init_history_store()
    safe_name = "".join(
        char if char.isalnum() or char in {".", "-", "_"} else "_"
        for char in record_name
    ).strip("._")
    if not safe_name:
        safe_name = "upload"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return storage.UPLOAD_DIR / f"{stamp}_{safe_name}"


def get_upload_retention_days() -> int:
    try:
        return int(os.getenv("UPLOAD_RETENTION_DAYS", str(DEFAULT_UPLOAD_RETENTION_DAYS)))
    except ValueError:
        return DEFAULT_UPLOAD_RETENTION_DAYS


def delete_stored_file(file_path: str) -> None:
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError:
        pass


__all__ = [
    "cleanup_expired_uploads",
    "delete_history_record",
    "get_upload_retention_days",
    "stored_upload_path",
]
