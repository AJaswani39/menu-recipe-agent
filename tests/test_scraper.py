import unittest
from unittest.mock import patch

import httpx
from bs4 import BeautifulSoup

from app.menu_parser import extract_menu_items, extract_price
from app.scrape_security import reject_private_destination
from app.scraper import scrape_menu


class FakeAsyncClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requested_urls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, url, **kwargs):
        self.requested_urls.append(url)
        return self.responses.pop(0)


class ScraperTests(unittest.TestCase):
    def test_extract_price(self):
        self.assertEqual(extract_price("Spicy Rigatoni $18"), "$18")
        self.assertEqual(extract_price("Burger $14.50 fries"), "$14.50")
        self.assertIsNone(extract_price("No price here"))

    def test_extract_menu_items_with_context(self):
        html = """
        <html>
          <head><title>Test Cafe</title></head>
          <body>
            <h2>Pasta</h2>
            <div class="menu-item">
              <h3>Spicy Rigatoni</h3>
              <p>Vodka sauce, basil, parmesan</p>
              <span>$18</span>
            </div>
            <div class="menu-item">
              <h3>Spicy Rigatoni</h3>
              <p>Vodka sauce, basil, parmesan</p>
              <span>$18</span>
            </div>
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        items = extract_menu_items(soup, "https://example.com/menu")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "Spicy Rigatoni")
        self.assertEqual(items[0].description, "Vodka sauce, basil, parmesan")
        self.assertEqual(items[0].price, "$18")
        self.assertEqual(items[0].category, "Pasta")

    def test_reject_private_destination(self):
        with self.assertRaises(ValueError):
            reject_private_destination("127.0.0.1")


class ScrapeMenuRedirectTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_private_redirect_destination(self):
        redirect = httpx.Response(
            302,
            headers={"location": "http://127.0.0.1/admin"},
            request=httpx.Request("GET", "https://example.test/menu"),
        )
        fake_client = FakeAsyncClient([redirect])

        def reject_private_only(hostname):
            if hostname == "127.0.0.1":
                raise ValueError("restaurant_url cannot target private or local networks")

        with (
            patch("app.scrape_fetcher.httpx.AsyncClient", return_value=fake_client),
            patch("app.scrape_security.reject_private_destination", side_effect=reject_private_only),
        ):
            with self.assertRaises(ValueError):
                await scrape_menu("https://example.test/menu")

        self.assertEqual(fake_client.requested_urls, ["https://example.test/menu"])

    async def test_follows_valid_redirect_and_extracts_menu(self):
        redirect = httpx.Response(
            302,
            headers={"location": "/real-menu"},
            request=httpx.Request("GET", "https://example.test/menu"),
        )
        html = """
        <html>
          <head><title>Redirect Cafe</title></head>
          <body>
            <div class="menu-item"><h3>Tomato Soup</h3><span>$9</span></div>
          </body>
        </html>
        """
        final = httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text=html,
            request=httpx.Request("GET", "https://example.test/real-menu"),
        )
        fake_client = FakeAsyncClient([redirect, final])

        with (
            patch("app.scrape_fetcher.httpx.AsyncClient", return_value=fake_client),
            patch("app.scrape_security.reject_private_destination"),
        ):
            menu = await scrape_menu("https://example.test/menu")

        self.assertEqual(
            fake_client.requested_urls,
            ["https://example.test/menu", "https://example.test/real-menu"],
        )
        self.assertEqual(menu.restaurant, "Redirect Cafe (example.test)")
        self.assertEqual(menu.menu_items[0].name, "Tomato Soup")


if __name__ == "__main__":
    unittest.main()
