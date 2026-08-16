import tempfile
from pathlib import Path

from app import storage
from app.history_repository import (
    create_history_record,
    get_history_record,
    list_history,
    update_history_recipe,
)
from app.history_uploads import (
    cleanup_expired_uploads,
    delete_history_record,
    stored_upload_path,
)
from app.history_schema import init_history_store


class HistoryStoreSandbox:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_storage_data_dir = storage.DATA_DIR
        self.old_storage_upload_dir = storage.UPLOAD_DIR
        self.old_storage_db_path = storage.DB_PATH
        root = Path(self.tmp.name)
        storage.DATA_DIR = root
        storage.UPLOAD_DIR = root / "uploads"
        storage.DB_PATH = root / "history.sqlite3"

    def tearDown(self):
        storage.DATA_DIR = self.old_storage_data_dir
        storage.UPLOAD_DIR = self.old_storage_upload_dir
        storage.DB_PATH = self.old_storage_db_path
        self.tmp.cleanup()
