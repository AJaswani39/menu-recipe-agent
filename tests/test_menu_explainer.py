import unittest
from unittest.mock import AsyncMock, patch

from app.gemini import GeminiConfigError
from app.menu_explainer import explain_menu_item
from app.models import MenuItem, MenuItemExplanationRequest


class MenuExplainerTests(unittest.IsolatedAsyncioTestCase):
    async def test_fallback_explanation_infers_common_allergens(self):
        with patch(
            "app.menu_explainer.configured_api_key",
            side_effect=GeminiConfigError("missing"),
        ):
            explanation = await explain_menu_item(
                MenuItemExplanationRequest(
                    item=MenuItem(
                        id="alfredo",
                        name="Chicken Alfredo",
                        description="Cream sauce, parmesan, fettuccine pasta",
                        category="Pasta",
                    )
                )
            )

        self.assertEqual(explanation.confidence, "estimated")
        self.assertIn("dairy", explanation.likely_allergens)
        self.assertIn("gluten", explanation.likely_allergens)

    async def test_gemini_explanation_is_normalized(self):
        gemini_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    '{"summary":"A bright pasta.","flavor_profile":["bright"],'
                                    '"likely_allergens":["gluten"],"substitutions":["rice pasta"],'
                                    '"confidence":"similar"}'
                                )
                            }
                        ]
                    }
                }
            ]
        }
        with (
            patch("app.menu_explainer.configured_api_key", return_value="key"),
            patch("app.menu_explainer.gemini_model", return_value="test-model"),
            patch("app.menu_explainer.generate_content", new=AsyncMock(return_value=gemini_payload)),
        ):
            explanation = await explain_menu_item(
                MenuItemExplanationRequest(
                    item=MenuItem(id="pasta", name="Lemon Pasta"),
                    restaurant_name="Test Cafe",
                )
            )

        self.assertEqual(explanation.summary, "A bright pasta.")
        self.assertEqual(explanation.flavor_profile, ["bright"])
        self.assertEqual(explanation.source, "Google Gemini (test-model)")


if __name__ == "__main__":
    unittest.main()
