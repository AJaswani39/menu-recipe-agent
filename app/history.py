from app import storage
from app.history_repository import (
    create_history_record,
    get_history_record,
    get_user_stored_bytes,
    list_history,
    update_history_recipe,
)
from app.history_schema import init_history_store
from app.history_uploads import (
    cleanup_expired_uploads,
    delete_history_record,
    get_upload_retention_days,
    stored_upload_path,
)

# Compatibility aliases for existing tests and callers that patch these paths.
DATA_DIR = storage.DATA_DIR
UPLOAD_DIR = storage.UPLOAD_DIR
DB_PATH = storage.DB_PATH

__all__ = [
    "DB_PATH",
    "DATA_DIR",
    "UPLOAD_DIR",
    "cleanup_expired_uploads",
    "create_history_record",
    "delete_history_record",
    "get_history_record",
    "get_upload_retention_days",
    "get_user_stored_bytes",
    "init_history_store",
    "list_history",
    "stored_upload_path",
    "update_history_recipe",
]
