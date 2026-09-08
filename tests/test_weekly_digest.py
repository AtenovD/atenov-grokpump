from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from bot.services.backtest import BacktestReport
from bot.services.weekly_digest import format_weekly_digest, publish_weekly_digest


def report() -> BacktestReport:
    return BacktestReport(
        total_signals=20, total_bought=4, total_skipped=16,
        skip_by_stage={"filter": 10, "checker": 6},
        win_rate=0.75, avg_pnl_pct=12.5, median_pnl_pct=8.0,
        best_position={"mint": "best", "symbol": "WIN", "pnl_pct": 40.0},
        worst_position={"mint": "worst", "symbol": "LOSS", "pnl_pct": -25.0},
        stop_loss_hit_rate=0.25, period_start=0, period_end=604800,
    )


class WeeklyDigestTests(unittest.IsolatedAsyncioTestCase):
    def test_format_contains_public_summary(self) -> None:
        text = format_weekly_digest(report())
        self.assertIn("Signals screened: <b>20</b>", text)
        self.assertIn("75.0%", text)
        self.assertIn("WIN (+40.0%)", text)
        self.assertIn("All positions are simulated", text)

    async def test_publish_uses_seven_day_backtest_and_separate_chat(self) -> None:
        bot = AsyncMock()
        with patch("bot.services.weekly_digest.run_backtest", new=AsyncMock(return_value=report())) as run:
            await publish_weekly_digest(bot, object(), "@public")
        run.assert_awaited_once_with(unittest.mock.ANY, since_days=7)
        bot.send_message.assert_awaited_once()
        self.assertEqual(bot.send_message.await_args.args[0], "@public")


if __name__ == "__main__":
    unittest.main()
