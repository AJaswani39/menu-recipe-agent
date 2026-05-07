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


if __name__ == "__main__":
    unittest.main()
