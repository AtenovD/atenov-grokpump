from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("BOT_TOKEN", "test-token")

from bot.services.onboarding import setup_checklist


class SetupChecklistTests(unittest.TestCase):
    def test_lists_both_items_when_nothing_is_configured(self) -> None:
        with patch("bot.services.onboarding.config") as mock_config:
            mock_config.grok_api_key = ""
            mock_config.alert_chat_id = None
            text = setup_checklist("en")
        self.assertIn("GROK_API_KEY", text)
        self.assertIn("ALERT_CHAT_ID", text)
        self.assertIn("console.x.ai", text)

    def test_lists_only_missing_item(self) -> None:
        with patch("bot.services.onboarding.config") as mock_config:
            mock_config.grok_api_key = "xai-configured"
            mock_config.alert_chat_id = None
            text = setup_checklist("en")
        self.assertNotIn("GROK_API_KEY", text)
        self.assertIn("ALERT_CHAT_ID", text)

    def test_returns_none_once_fully_configured(self) -> None:
        with patch("bot.services.onboarding.config") as mock_config:
            mock_config.grok_api_key = "xai-configured"
            mock_config.alert_chat_id = "-100123"
            self.assertIsNone(setup_checklist("en"))

    def test_renders_in_russian(self) -> None:
        with patch("bot.services.onboarding.config") as mock_config:
            mock_config.grok_api_key = ""
            mock_config.alert_chat_id = None
            text = setup_checklist("ru")
        self.assertIn("Получить ключ", text)


if __name__ == "__main__":
    unittest.main()
