from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from bot.services.models import AgentVerdict, RiskDecision, Token, TokenAnalysis
from bot.services.webhooks import deliver_signal_webhooks, signal_payload


def analysis() -> TokenAnalysis:
    token = Token("mint", "TST", "Test", "creator", 2.0, 9, 100.0, chain="base")
    verdict = AgentVerdict("auditor", 0.8, "ok")
    return TokenAnalysis(
        token, verdict, verdict, verdict, verdict, verdict, 0.8,
        RiskDecision(True, "within_limits", 0.2),
    )


class Response:
    def __init__(self, status: int) -> None:
        self.status = status
        self.request_info = None
        self.history = ()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class Session:
    def __init__(self, statuses: list[int]) -> None:
        self.statuses = statuses
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response(self.statuses.pop(0))


class WebhookTests(unittest.IsolatedAsyncioTestCase):
    def test_v1_payload_contains_complete_analysis(self) -> None:
        payload = signal_payload(analysis(), emitted_at=123)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["event"], "signal.passed")
        self.assertEqual(payload["emitted_at"], 123)
        self.assertEqual(payload["analysis"]["token"]["chain"], "base")
        self.assertEqual(payload["analysis"]["risk"]["size_sol"], 0.2)

    async def test_failed_delivery_is_retried_once(self) -> None:
        session = Session([500, 204])
        with patch("bot.services.webhooks.asyncio.sleep", new=AsyncMock()) as sleep:
            await deliver_signal_webhooks(session, analysis(), ("https://example.test/hook",))
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(session.calls[0][1]["json"]["schema_version"], 1)
        sleep.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
