import os
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import app.history as history
from app.auth import create_user
from app.main import create_app
from helpers import HistoryStoreSandbox


class AuthHardeningTests(HistoryStoreSandbox, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.user, self.token = create_user("Auth Tester")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.client = TestClient(create_app())

    def tearDown(self):
        super().tearDown()

    def test_protected_endpoints_reject_missing_and_invalid_tokens(self):
        self.assertEqual(self.client.get("/history").status_code, 401)
        self.assertEqual(
            self.client.get("/history", headers={"Authorization": "Bearer bad"}).status_code,
            401,
        )

    def test_valid_bearer_token_can_call_protected_endpoint(self):
        response = self.client.get("/history", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"items": []})

    def test_menu_scrape_requires_bearer_token(self):
        response = self.client.get(
            "/menu", params={"restaurant_url": "https://example.test/menu"}
        )

        self.assertEqual(response.status_code, 401)

    def test_valid_bearer_token_can_call_menu_scrape(self):
        menu = {
            "restaurant": "Test Cafe",
            "source_url": "https://example.test/menu",
            "menu_items": [{"id": "abc", "name": "Soup"}],
        }
        with patch("app.routes.menu.scrape_menu", new=AsyncMock(return_value=menu)):
            response = self.client.get(
                "/menu",
                params={"restaurant_url": "https://example.test/menu"},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["restaurant"], "Test Cafe")

    def test_token_is_stored_hashed(self):
        with closing(sqlite3.connect(history.DB_PATH)) as conn:
            row = conn.execute("SELECT token_hash FROM auth_users").fetchone()

        self.assertIsNotNone(row)
        self.assertNotEqual(row[0], self.token)
        self.assertEqual(len(row[0]), 64)

    def test_recipe_rate_limit_returns_429(self):
        payload = {"dish_name": "Soup"}
        with patch.dict(os.environ, {"RECIPE_RATE_LIMIT_PER_MINUTE": "1"}):
            with patch("app.routes.menu.get_recipe", new=AsyncMock(return_value={"dish": "Soup"})):
                first = self.client.post("/recipe", json=payload, headers=self.headers)
                second = self.client.post("/recipe", json=payload, headers=self.headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)


class ProductionHardeningTests(HistoryStoreSandbox, unittest.TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_docs_disabled_in_production_and_headers_present(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            client = TestClient(create_app())

        docs = client.get("/docs")
        health = client.get("/health")

        self.assertEqual(docs.status_code, 404)
        self.assertEqual(health.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(health.headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(health.headers["X-Frame-Options"], "DENY")

    def test_cors_uses_configured_origins(self):
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "https://example.test"}):
            client = TestClient(create_app())

        response = client.options(
            "/history",
            headers={
                "Origin": "https://example.test",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        self.assertEqual(response.headers["access-control-allow-origin"], "https://example.test")


if __name__ == "__main__":
    unittest.main()
