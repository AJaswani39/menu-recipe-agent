import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = Path("/tmp/menu-recipe-agent") if os.getenv("VERCEL") else PROJECT_ROOT / "data"

DATA_DIR = DEFAULT_DATA_DIR
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "history.sqlite3"


def ensure_storage_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
