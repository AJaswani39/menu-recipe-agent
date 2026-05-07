import sqlite3
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone

import app.history as history
from app.auth import create_user
from app.models import MenuItem, MenuScrapeResponse, RecipeResponse
from helpers import HistoryStoreSandbox


class HistoryStoreTests(HistoryStoreSandbox, unittest.TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_create_list_update_and_delete_history(self):
        user, _token = create_user("Test User")
        upload_path = history.stored_upload_path("menu.png")
        upload_path.write_bytes(b"fake")
        menu = MenuScrapeResponse(
            restaurant="Test Cafe",
            source_url="upload://menu.png",
            menu_items=[
                MenuItem(id="abc", name="Tacos", price="$12", url="upload://menu.png")
            ],
        )

        record = history.create_history_record(
            owner_user_id=user.id,
            source_type="upload",
            restaurant=menu.restaurant,
            source_label="menu.png",
            file_name="menu.png",
            mime_type="image/png",
            file_path=str(upload_path),
            menu=menu,
        )
        self.assertEqual(record.menu_item_count, 1)
        self.assertIsInstance(record.id, str)
        self.assertEqual(len(history.list_history(user.id)), 1)

        updated = history.update_history_recipe(
            user.id,
            record.id,
            RecipeResponse(
                dish="Tacos",
                ingredients=["tortilla"],
                steps=["warm"],
                source="test",
                confidence="similar",
            ),
        )
        self.assertEqual(updated.recipe.dish, "Tacos")

        self.assertTrue(history.delete_history_record(user.id, record.id))
        self.assertFalse(upload_path.exists())
        self.assertEqual(history.list_history(user.id), [])

    def test_history_is_owner_scoped(self):
        user_a, _ = create_user("User A")
        user_b, _ = create_user("User B")
        menu = MenuScrapeResponse(
            restaurant="Private Cafe",
            source_url="upload://menu.png",
            menu_items=[MenuItem(id="abc", name="Soup")],
        )

        record = history.create_history_record(
            owner_user_id=user_a.id,
            source_type="upload",
            restaurant=menu.restaurant,
            source_label="menu.png",
            menu=menu,
        )

        self.assertEqual(len(history.list_history(user_a.id)), 1)
        self.assertEqual(history.list_history(user_b.id), [])
        self.assertIsNone(history.get_history_record(user_b.id, record.id))
        self.assertFalse(history.delete_history_record(user_b.id, record.id))

    def test_corrupt_history_json_does_not_crash_reads(self):
        user, _ = create_user("Legacy User")
        history.init_history_store()
        created_at = datetime.now(timezone.utc).isoformat()
        with closing(sqlite3.connect(history.DB_PATH)) as conn:
            conn.execute(
                """
                INSERT INTO history (
                    owner_user_id, public_id, source_type, restaurant, source_label,
                    menu_json, recipe_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    "bad-json-record",
                    "upload",
                    "Legacy Cafe",
                    "old-menu.png",
                    "{not valid json",
                    "{also not valid json",
                    created_at,
                ),
            )
            conn.commit()

        summaries = history.list_history(user.id)
        record = history.get_history_record(user.id, "bad-json-record")

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0].menu_item_count, 0)
        self.assertIsNone(summaries[0].recipe_dish)
        self.assertIsNotNone(record)
        self.assertIsNone(record.menu)
        self.assertIsNone(record.recipe)

    def test_invalid_legacy_history_models_do_not_crash_detail_reads(self):
        user, _ = create_user("Legacy Shape User")
        history.init_history_store()
        created_at = datetime.now(timezone.utc).isoformat()
        with closing(sqlite3.connect(history.DB_PATH)) as conn:
            conn.execute(
                """
                INSERT INTO history (
                    owner_user_id, public_id, source_type, restaurant, source_label,
                    menu_json, recipe_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    "invalid-model-record",
                    "upload",
                    "Legacy Cafe",
                    "old-menu.png",
                    '{"restaurant": "Legacy Cafe"}',
                    '{"dish": "Soup"}',
                    created_at,
                ),
            )
            conn.commit()

        record = history.get_history_record(user.id, "invalid-model-record")

        self.assertIsNotNone(record)
        self.assertEqual(record.menu_item_count, 0)
        self.assertIsNone(record.menu)
        self.assertIsNone(record.recipe)

    def test_cleanup_expired_uploads_only_deletes_old_upload_files(self):
        user, _ = create_user("Retention User")
        old_upload_path = history.stored_upload_path("old-menu.png")
        old_upload_path.write_bytes(b"old")
        new_upload_path = history.stored_upload_path("new-menu.png")
        new_upload_path.write_bytes(b"new")
        menu = MenuScrapeResponse(
            restaurant="Retention Cafe",
            source_url="upload://menu.png",
            menu_items=[MenuItem(id="abc", name="Soup")],
        )

        old_record = history.create_history_record(
            owner_user_id=user.id,
            source_type="upload",
            restaurant=menu.restaurant,
            source_label="old-menu.png",
            file_path=str(old_upload_path),
            stored_bytes=3,
            menu=menu,
        )
        new_record = history.create_history_record(
            owner_user_id=user.id,
            source_type="upload",
            restaurant=menu.restaurant,
            source_label="new-menu.png",
            file_path=str(new_upload_path),
            stored_bytes=3,
            menu=menu,
        )
        recipe_record = history.create_history_record(
            owner_user_id=user.id,
            source_type="recipe",
            restaurant="Retention Cafe",
            source_label="recipe-only",
            recipe=RecipeResponse(
                dish="Soup",
                ingredients=["stock"],
                steps=["simmer"],
                source="test",
                confidence="similar",
            ),
        )
        old_created_at = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        with closing(sqlite3.connect(history.DB_PATH)) as conn:
            conn.execute(
                "UPDATE history SET created_at = ? WHERE public_id IN (?, ?)",
                (old_created_at, old_record.id, recipe_record.id),
            )
            conn.commit()

        deleted_count = history.cleanup_expired_uploads(retention_days=30)

        self.assertEqual(deleted_count, 1)
        self.assertFalse(old_upload_path.exists())
        self.assertTrue(new_upload_path.exists())
        self.assertIsNone(history.get_history_record(user.id, old_record.id))
        self.assertIsNotNone(history.get_history_record(user.id, new_record.id))
        self.assertIsNotNone(history.get_history_record(user.id, recipe_record.id))


if __name__ == "__main__":
    unittest.main()
