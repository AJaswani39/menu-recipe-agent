import unittest

from app.gemini import parse_json_response


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


if __name__ == "__main__":
    unittest.main()
