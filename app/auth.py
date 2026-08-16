import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Header, HTTPException, status

from app import storage

DEFAULT_USER_STORAGE_QUOTA_BYTES = 250 * 1024 * 1024
DEFAULT_UPLOAD_RATE_LIMIT_PER_MINUTE = 10
DEFAULT_MENU_RATE_LIMIT_PER_MINUTE = 20
DEFAULT_RECIPE_RATE_LIMIT_PER_MINUTE = 20


@dataclass(frozen=True)
class AuthUser:
    id: int
    public_id: str
    display_name: str
    storage_quota_bytes: int


def init_auth_store() -> None:
    storage.ensure_storage_dirs()
    with closing(_connect()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                public_id TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                storage_quota_bytes INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limits (
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                window_start INTEGER NOT NULL,
                request_count INTEGER NOT NULL,
                PRIMARY KEY (user_id, action, window_start)
            )
            """
        )
        conn.commit()


def create_user(display_name: str, storage_quota_bytes: int | None = None) -> tuple[AuthUser, str]:
    init_auth_store()
    token = secrets.token_urlsafe(32)
    public_id = secrets.token_urlsafe(16)
    quota = storage_quota_bytes or get_user_storage_quota_bytes()
    created_at = datetime.now(timezone.utc).isoformat()
    with closing(_connect()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO auth_users (
                public_id, display_name, token_hash, is_active,
                storage_quota_bytes, created_at
            )
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (public_id, display_name.strip(), hash_token(token), quota, created_at),
        )
        conn.commit()
        user_id = int(cursor.lastrowid)
    return (
        AuthUser(
            id=user_id,
            public_id=public_id,
            display_name=display_name.strip(),
            storage_quota_bytes=quota,
        ),
        token,
    )


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def authenticate_token(token: str) -> AuthUser | None:
    init_auth_store()
    candidate_hash = hash_token(token)
    with closing(_connect()) as conn:
        row = conn.execute(
            """
            SELECT id, public_id, display_name, token_hash, storage_quota_bytes
            FROM auth_users
            WHERE is_active = 1 AND token_hash = ?
            """,
            (candidate_hash,),
        ).fetchone()
    if row is None:
        return None
    if not hmac.compare_digest(row["token_hash"], candidate_hash):
        return None
    return AuthUser(
        id=row["id"],
        public_id=row["public_id"],
        display_name=row["display_name"],
        storage_quota_bytes=row["storage_quota_bytes"],
    )


def require_user(authorization: str | None = Header(default=None)) -> AuthUser:
    if not authorization:
        raise _auth_error()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise _auth_error()
    user = authenticate_token(token.strip())
    if user is None:
        raise _auth_error()
    return user


def enforce_rate_limit(user: AuthUser, action: str, limit: int) -> None:
    init_auth_store()
    if limit <= 0:
        return
    window_start = int(time.time() // 60) * 60
    with closing(_connect()) as conn:
        conn.execute(
            """
            INSERT INTO rate_limits (user_id, action, window_start, request_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, action, window_start)
            DO UPDATE SET request_count = request_count + 1
            """,
            (user.id, action, window_start),
        )
        row = conn.execute(
            """
            SELECT request_count
            FROM rate_limits
            WHERE user_id = ? AND action = ? AND window_start = ?
            """,
            (user.id, action, window_start),
        ).fetchone()
        conn.commit()
    if row and row["request_count"] > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again in a minute.",
        )


def get_user_storage_quota_bytes() -> int:
    return _env_int("USER_STORAGE_QUOTA_BYTES", DEFAULT_USER_STORAGE_QUOTA_BYTES)


def get_upload_rate_limit_per_minute() -> int:
    return _env_int("UPLOAD_RATE_LIMIT_PER_MINUTE", DEFAULT_UPLOAD_RATE_LIMIT_PER_MINUTE)


def get_menu_rate_limit_per_minute() -> int:
    return _env_int("MENU_RATE_LIMIT_PER_MINUTE", DEFAULT_MENU_RATE_LIMIT_PER_MINUTE)


def get_recipe_rate_limit_per_minute() -> int:
    return _env_int("RECIPE_RATE_LIMIT_PER_MINUTE", DEFAULT_RECIPE_RATE_LIMIT_PER_MINUTE)


def _connect() -> sqlite3.Connection:
    return storage.connect()


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid bearer token required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
