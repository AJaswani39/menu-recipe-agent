import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.gemini import (
    GeminiConfigError,
    check_config_status,
    configured_api_key,
    timeout_from_env,
)


class GeminiConfigTests(unittest.IsolatedAsyncioTestCase):
    def test_configured_api_key_requires_env_var(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(GeminiConfigError):
                configured_api_key()

    def test_timeout_from_env_uses_default_for_invalid_values(self):
        with patch.dict("os.environ", {"BAD_TIMEOUT": "not-a-number"}):
            self.assertEqual(timeout_from_env("BAD_TIMEOUT", 4.5), 4.5)
        with patch.dict("os.environ", {"BAD_TIMEOUT": "-1"}):
            self.assertEqual(timeout_from_env("BAD_TIMEOUT", 4.5), 4.5)

    async def test_check_config_status_reports_missing_key(self):
        with patch.dict("os.environ", {}, clear=True):
            status = await check_config_status()

        self.assertFalse(status["configured"])
        self.assertFalse(status["reachable"])
        self.assertEqual(status["detail"], "GEMINI_API_KEY is not set")

    async def test_check_config_status_reports_http_error(self):
        response = httpx.Response(
            403,
            request=httpx.Request("POST", "https://example.test/gemini"),
        )
        error = httpx.HTTPStatusError("forbidden", request=response.request, response=response)
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True),
            patch("app.gemini.generate_content", new=AsyncMock(side_effect=error)),
        ):
            status = await check_config_status()

        self.assertTrue(status["configured"])
        self.assertFalse(status["reachable"])
        self.assertEqual(status["detail"], "Gemini API returned HTTP 403")

    async def test_check_config_status_reports_success(self):
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True),
            patch("app.gemini.generate_content", new=AsyncMock(return_value={"ok": True})),
        ):
            status = await check_config_status()

        self.assertTrue(status["configured"])
        self.assertTrue(status["reachable"])
        self.assertEqual(status["detail"], "Gemini API reachable")


if __name__ == "__main__":
    unittest.main()
