import unittest
from unittest.mock import AsyncMock, patch

from app.gemini import parse_json_response
from app.models import DishSelectionRequest
from app.recipe import get_recipe


class RecipeParsingTests(unittest.TestCase):
    def test_parse_plain_json_response(self):
        parsed = parse_json_response(
            '{"ingredients": ["salt"], "steps": ["season"], "confidence": "similar"}'
        )

        self.assertEqual(parsed["ingredients"], ["salt"])

    def test_parse_fenced_json_response(self):
        parsed = parse_json_response(
            'Here is JSON:\n```json\n{"ingredients":["flour"],"steps":["mix"]}\n```'
        )

        self.assertEqual(parsed["steps"], ["mix"])


class RecipeGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_recipe_response_preserves_requested_servings(self):
        with patch("app.recipe._get_recipe_from_gemini", new=AsyncMock(return_value=None)):
            recipe = await get_recipe(
                DishSelectionRequest(dish_name="Chicken Alfredo", servings=6)
            )

        self.assertEqual(recipe.servings, 6)


if __name__ == "__main__":
    unittest.main()
