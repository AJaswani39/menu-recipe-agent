import tempfile
from pathlib import Path

import app.history as history
from app import storage


class HistoryStoreSandbox:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_data_dir = history.DATA_DIR
        self.old_upload_dir = history.UPLOAD_DIR
        self.old_db_path = history.DB_PATH
        self.old_storage_data_dir = storage.DATA_DIR
        self.old_storage_upload_dir = storage.UPLOAD_DIR
        self.old_storage_db_path = storage.DB_PATH
        root = Path(self.tmp.name)
        history.DATA_DIR = root
        history.UPLOAD_DIR = root / "uploads"
        history.DB_PATH = root / "history.sqlite3"
        storage.DATA_DIR = history.DATA_DIR
        storage.UPLOAD_DIR = history.UPLOAD_DIR
        storage.DB_PATH = history.DB_PATH

    def tearDown(self):
        history.DATA_DIR = self.old_data_dir
        history.UPLOAD_DIR = self.old_upload_dir
        history.DB_PATH = self.old_db_path
        storage.DATA_DIR = self.old_storage_data_dir
        storage.UPLOAD_DIR = self.old_storage_upload_dir
        storage.DB_PATH = self.old_storage_db_path
        self.tmp.cleanup()
