from __future__ import annotations

import time
import unittest

from bot.services.backtest import run_backtest
from bot.services.storage import Position, Storage


class BacktestTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.storage = Storage(":memory:")
        await self.storage.connect()

    async def asyncTearDown(self) -> None:
        await self.storage.close()

    async def test_empty_database(self) -> None:
        report = await run_backtest(self.storage)
        self.assertEqual(report.total_signals, 0)
        self.assertEqual(report.total_bought, 0)
        self.assertEqual(report.total_skipped, 0)
        self.assertEqual(report.skip_by_stage, {})
        self.assertEqual(report.win_rate, 0.0)
        self.assertIsNone(report.best_position)
        self.assertIsNone(report.worst_position)

    async def test_mixed_wins_and_losses(self) -> None:
        await self.storage.log_signal("win", "WIN", 0.8, "executor", "bought")
        await self.storage.log_signal("loss", "LOSS", 0.7, "executor", "bought")
        await self.storage.log_signal("skip", "SKIP", 0.3, "scoring", "skip")
        await self.storage.open_position(Position("win", "WIN", 1.0, 0.1, 0.8, "a", 1, "open"))
        await self.storage.open_position(Position("loss", "LOSS", 2.0, 0.1, 0.7, "b", 2, "open"))
        await self.storage.close_position("win", 1.5, "take_profit")
        await self.storage.close_position("loss", 1.0, "stop_loss")

        report = await run_backtest(self.storage)
        self.assertEqual(report.total_signals, 3)
        self.assertEqual(report.total_bought, 2)
        self.assertEqual(report.total_skipped, 1)
        self.assertEqual(report.skip_by_stage, {"scoring": 1})
        self.assertEqual(report.win_rate, 0.5)
        self.assertAlmostEqual(report.avg_pnl_pct, 0.0)
        self.assertAlmostEqual(report.median_pnl_pct, 0.0)
        self.assertEqual(report.best_position["mint"], "win")
        self.assertEqual(report.worst_position["mint"], "loss")
        self.assertEqual(report.stop_loss_hit_rate, 0.5)

    async def test_since_days_excludes_old_rows(self) -> None:
        now = int(time.time())
        await self.storage.db.execute(
            "INSERT INTO signals (mint, symbol, score, stage, outcome, detail, created_at) "
            "VALUES ('old', 'OLD', 0.1, 'filter', 'skip', '', ?)",
            (now - 10 * 86400,),
        )
        await self.storage.log_signal("new", "NEW", 0.1, "filter", "skip")
        await self.storage.db.execute(
            "INSERT INTO positions (mint, symbol, entry_price, sol_spent, score, creator, opened_at, "
            "status, exit_price, closed_at, close_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("old", "OLD", 1.0, 0.1, 0.5, "a", now - 10 * 86400, "closed", 2.0, now - 9 * 86400, "take_profit"),
        )
        await self.storage.db.commit()

        report = await run_backtest(self.storage, since_days=1)
        self.assertEqual(report.total_signals, 1)
        self.assertEqual(report.total_skipped, 1)
        self.assertIsNone(report.best_position)


if __name__ == "__main__":
    unittest.main()
