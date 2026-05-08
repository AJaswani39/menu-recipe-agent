import tempfile
import unittest
from pathlib import Path

from app.upload_extractor import (
    SUPPORTED_MIME_TYPES,
    _inline_payload,
    _menu_from_parsed,
)


class UploadExtractorTests(unittest.TestCase):
    def test_supported_mime_types(self):
        self.assertIn("image/png", SUPPORTED_MIME_TYPES)
        self.assertIn("image/jpeg", SUPPORTED_MIME_TYPES)
        self.assertIn("application/pdf", SUPPORTED_MIME_TYPES)

    def test_inline_payload_contains_base64_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "menu.png"
            path.write_bytes(b"menu")

            payload = _inline_payload(path, "image/png", "Test Cafe")

        inline = payload["contents"][0]["parts"][0]["inline_data"]
        self.assertEqual(inline["mime_type"], "image/png")
        self.assertEqual(inline["data"], "bWVudQ==")

    def test_menu_from_parsed_normalizes_items(self):
        menu = _menu_from_parsed(
            {
                "restaurant": "Test Cafe",
                "menu_items": [
                    {
                        "name": "Burger",
                        "description": "Cheddar",
                        "price": "$14",
                        "category": "Mains",
                    }
                ],
            },
            "menu.png",
            None,
        )

        self.assertEqual(menu.restaurant, "Test Cafe")
        self.assertEqual(menu.menu_items[0].name, "Burger")
        self.assertEqual(menu.menu_items[0].price, "$14")


if __name__ == "__main__":
    unittest.main()
