import unittest

from pydantic import ValidationError

from app.models import AgentRunRequest, MenuItem


class ModelTests(unittest.TestCase):
    def test_agent_request_accepts_selected_item(self):
        request = AgentRunRequest(
            restaurant_url="https://example.com/menu",
            dish_name="Burger",
            selected_item=MenuItem(
                id="abc123",
                name="Burger",
                description="Cheddar and pickles",
                price="$15",
                category="Mains",
                url="https://example.com/menu",
            ),
        )

        self.assertEqual(request.selected_item.price, "$15")

    def test_agent_request_rejects_blank_dish(self):
        with self.assertRaises(ValidationError):
            AgentRunRequest(restaurant_url="https://example.com/menu", dish_name=" ")

    def test_agent_request_normalizes_recipe_customizations(self):
        request = AgentRunRequest(
            restaurant_url="https://example.com/menu",
            dish_name="Burger",
            servings=2,
            dietary_preference=" vegetarian ",
            spice_level=" ",
            equipment=" skillet ",
            time_limit_minutes=30,
        )

        self.assertEqual(request.servings, 2)
        self.assertEqual(request.dietary_preference, "vegetarian")
        self.assertIsNone(request.spice_level)
        self.assertEqual(request.equipment, "skillet")
        self.assertEqual(request.time_limit_minutes, 30)

    def test_agent_request_rejects_invalid_servings(self):
        with self.assertRaises(ValidationError):
            AgentRunRequest(
                restaurant_url="https://example.com/menu",
                dish_name="Burger",
                servings=0,
            )


if __name__ == "__main__":
    unittest.main()
