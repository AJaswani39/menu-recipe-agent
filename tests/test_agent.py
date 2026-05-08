import unittest
from unittest.mock import AsyncMock, patch

from app.agent import run_agent_request
from app.models import AgentRunRequest, MenuItem, MenuScrapeResponse, RecipeResponse


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_agent_reuses_request_menu(self):
        menu = MenuScrapeResponse(
            restaurant="Test Cafe",
            source_url="https://example.com/menu",
            menu_items=[
                MenuItem(
                    id="spicy-rigatoni",
                    name="Spicy Rigatoni",
                    description="Vodka sauce, basil, parmesan",
                    price="$18",
                    category="Pasta",
                    url="https://example.com/menu",
                )
            ],
        )
        recipe = RecipeResponse(
            dish="Spicy Rigatoni",
            ingredients=["pasta"],
            steps=["cook"],
            source="test",
            confidence="similar",
        )
        request = AgentRunRequest(
            restaurant_url="https://example.com/menu",
            dish_name="Spicy Rigatoni",
            menu=menu,
            servings=2,
            dietary_preference="vegetarian",
            spice_level="medium",
            equipment="dutch oven",
            time_limit_minutes=45,
        )

        with (
            patch("app.agent.scrape_menu", new=AsyncMock()) as scrape_menu,
            patch("app.agent.get_recipe", new=AsyncMock(return_value=recipe)) as get_recipe,
        ):
            returned_menu, returned_recipe = await run_agent_request(request, owner_user_id=1)

        scrape_menu.assert_not_awaited()
        recipe_selection = get_recipe.await_args.args[0]
        self.assertEqual(recipe_selection.servings, 2)
        self.assertEqual(recipe_selection.dietary_preference, "vegetarian")
        self.assertEqual(recipe_selection.spice_level, "medium")
        self.assertEqual(recipe_selection.equipment, "dutch oven")
        self.assertEqual(recipe_selection.time_limit_minutes, 45)
        self.assertEqual(returned_menu.restaurant, "Test Cafe")
        self.assertEqual(returned_recipe.dish, "Spicy Rigatoni")


if __name__ == "__main__":
    unittest.main()
