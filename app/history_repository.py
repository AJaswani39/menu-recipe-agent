import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from pydantic import ValidationError

from app import storage
from app.history_ids import new_public_id
from app.history_schema import init_history_store
from app.models import HistoryRecord, HistorySummary, MenuScrapeResponse, RecipeResponse


def create_history_record(
    *,
    owner_user_id: int,
    source_type: str,
    restaurant: str,
    source_label: str,
    source_url: str | None = None,
    file_name: str | None = None,
    mime_type: str | None = None,
    file_path: str | None = None,
    stored_bytes: int = 0,
    menu: MenuScrapeResponse | None = None,
    recipe: RecipeResponse | None = None,
) -> HistoryRecord:
    init_history_store()
    created_at = datetime.now(timezone.utc).isoformat()
    public_id = new_public_id()
    with closing(storage.connect()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO history (
                owner_user_id, public_id, source_type, restaurant, source_label,
                source_url, file_name, mime_type, file_path, stored_bytes,
                menu_json, recipe_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_user_id,
                public_id,
                source_type,
                restaurant,
                source_label,
                source_url,
                file_name,
                mime_type,
                file_path,
                stored_bytes,
                dump_model(menu),
                dump_model(recipe),
                created_at,
            ),
        )
        record_id = int(cursor.lastrowid)
        conn.commit()
    record = get_history_record(owner_user_id, public_id)
    if record is None:
        raise RuntimeError(f"Saved history record {record_id} could not be reloaded")
    return record


def update_history_recipe(
    owner_user_id: int, public_id: str, recipe: RecipeResponse
) -> HistoryRecord | None:
    init_history_store()
    with closing(storage.connect()) as conn:
        conn.execute(
            """
            UPDATE history
            SET recipe_json = ?
            WHERE owner_user_id = ? AND public_id = ? AND deleted_at IS NULL
            """,
            (dump_model(recipe), owner_user_id, public_id),
        )
        conn.commit()
    return get_history_record(owner_user_id, public_id)


def list_history(owner_user_id: int) -> list[HistorySummary]:
    init_history_store()
    with closing(storage.connect()) as conn:
        rows = conn.execute(
            """
            SELECT public_id, source_type, restaurant, source_label, created_at,
                   menu_json, recipe_json
            FROM history
            WHERE owner_user_id = ? AND deleted_at IS NULL
            ORDER BY id DESC
            LIMIT 50
            """,
            (owner_user_id,),
        ).fetchall()
    return [summary_from_row(row) for row in rows]


def get_history_record(owner_user_id: int, public_id: str) -> HistoryRecord | None:
    init_history_store()
    with closing(storage.connect()) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM history
            WHERE owner_user_id = ? AND public_id = ? AND deleted_at IS NULL
            """,
            (owner_user_id, public_id),
        ).fetchone()
    if row is None:
        return None
    return record_from_row(row)


def mark_history_deleted(owner_user_id: int, public_id: str) -> str | None:
    init_history_store()
    with closing(storage.connect()) as conn:
        row = conn.execute(
            """
            SELECT file_path
            FROM history
            WHERE owner_user_id = ? AND public_id = ? AND deleted_at IS NULL
            """,
            (owner_user_id, public_id),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            """
            UPDATE history
            SET deleted_at = ?
            WHERE owner_user_id = ? AND public_id = ?
            """,
            (datetime.now(timezone.utc).isoformat(), owner_user_id, public_id),
        )
        conn.commit()
    return row["file_path"]


def get_user_stored_bytes(owner_user_id: int) -> int:
    init_history_store()
    with closing(storage.connect()) as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(stored_bytes), 0) AS total
            FROM history
            WHERE owner_user_id = ? AND deleted_at IS NULL
            """,
            (owner_user_id,),
        ).fetchone()
    return int(row["total"] if row else 0)


def dump_model(model) -> str | None:
    if model is None:
        return None
    return model.model_dump_json()


def load_json(value: str | None) -> dict | None:
    if not value:
        return None
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def summary_from_row(row: sqlite3.Row) -> HistorySummary:
    menu_data = load_json(row["menu_json"])
    recipe_data = load_json(row["recipe_json"])
    recipe_dish = recipe_data.get("dish") if recipe_data else None
    menu_item_count = len(menu_data.get("menu_items", [])) if menu_data else 0
    return HistorySummary(
        id=row["public_id"],
        source_type=row["source_type"],
        restaurant=row["restaurant"],
        source_label=row["source_label"],
        created_at=row["created_at"],
        menu_item_count=menu_item_count,
        recipe_dish=recipe_dish,
    )


def record_from_row(row: sqlite3.Row) -> HistoryRecord:
    menu_data = load_json(row["menu_json"])
    recipe_data = load_json(row["recipe_json"])
    return HistoryRecord(
        id=row["public_id"],
        source_type=row["source_type"],
        restaurant=row["restaurant"],
        source_label=row["source_label"],
        created_at=row["created_at"],
        menu_item_count=len(menu_data.get("menu_items", [])) if menu_data else 0,
        recipe_dish=recipe_data.get("dish") if recipe_data else None,
        source_url=row["source_url"],
        file_name=row["file_name"],
        mime_type=row["mime_type"],
        menu=safe_model(MenuScrapeResponse, menu_data),
        recipe=safe_model(RecipeResponse, recipe_data),
    )


def safe_model(model_class, data: dict | None):
    if not data:
        return None
    try:
        return model_class(**data)
    except ValidationError:
        return None
