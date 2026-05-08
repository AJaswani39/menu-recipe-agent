import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.auth import create_user
from app.main import app
from app.models import MenuItem, MenuScrapeResponse
from helpers import HistoryStoreSandbox


class UploadRouteTests(HistoryStoreSandbox, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.user, self.token = create_user("Upload Tester")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.client = TestClient(app)

    def tearDown(self):
        super().tearDown()

    def test_upload_menu_rejects_unsupported_type(self):
        response = self.client.post(
            "/uploads/menu",
            files={"file": ("menu.txt", b"hello", "text/plain")},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 400)

    def test_upload_menu_requires_bearer_token(self):
        response = self.client.post(
            "/uploads/menu",
            files={"file": ("menu.png", b"\x89PNG\r\n\x1a\nfake", "image/png")},
        )

        self.assertEqual(response.status_code, 401)

    def test_upload_menu_saves_history(self):
        menu = MenuScrapeResponse(
            restaurant="Test Cafe",
            source_url="upload://menu.png",
            menu_items=[
                MenuItem(id="abc", name="Burger", description="Cheddar")
            ],
        )
        with patch(
            "app.routes.uploads.extract_menu_from_upload",
            new=AsyncMock(return_value=menu),
        ):
            response = self.client.post(
                "/uploads/menu",
                files={"file": ("menu.png", b"\x89PNG\r\n\x1a\nfake", "image/png")},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["menu"]["restaurant"], "Test Cafe")
        self.assertEqual(body["history"]["menu_item_count"], 1)
        history_id = body["history"]["id"]
        self.assertIsInstance(history_id, str)

        detail = self.client.get(f"/history/{history_id}", headers=self.headers)
        self.assertEqual(detail.status_code, 200)

        deleted = self.client.delete(f"/history/{history_id}", headers=self.headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(
            self.client.get(f"/history/{history_id}", headers=self.headers).status_code,
            404,
        )

    def test_upload_menu_rejects_mismatched_content(self):
        response = self.client.post(
            "/uploads/menu",
            files={"file": ("menu.png", b"not really a png", "image/png")},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "Uploaded file contents do not match the declared file type.",
        )


if __name__ == "__main__":
    unittest.main()
