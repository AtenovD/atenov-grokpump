from __future__ import annotations

from bot.config import config
from bot.services.models import RiskDecision
from bot.services.storage import Storage

# Fraction of the remaining daily loss budget a single trade may risk.
MAX_SHARE_OF_REMAINING_BUDGET = 0.30
MIN_TRADE_SOL = 0.01


class RiskManager:
    """Five independent limits, checked before any dry-run trade is opened.

    This never calls Grok — it's plain arithmetic and is deliberately the
    last gate, so a good score can still be blocked by the day's numbers.
    """

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    async def evaluate(self, score: float) -> RiskDecision:
        trades_today, pnl_today = await self.storage.get_daily_counters()
        open_positions = await self.storage.open_position_count()

        if -pnl_today >= config.daily_loss_limit_sol:
            return RiskDecision(approved=False, reason="daily_loss_limit_hit")

        if trades_today >= config.max_trades_per_day:
            return RiskDecision(approved=False, reason="max_trades_per_day_hit")

        if open_positions >= config.max_open_positions:
            return RiskDecision(approved=False, reason="max_open_positions_hit")

        remaining_budget = config.daily_loss_limit_sol - max(0.0, -pnl_today)
        size = min(
            config.max_sol_per_trade * score,
            remaining_budget * MAX_SHARE_OF_REMAINING_BUDGET,
        )
        if size < MIN_TRADE_SOL:
            return RiskDecision(approved=False, reason="position_size_too_small")

        return RiskDecision(approved=True, reason="ok", size_sol=round(size, 4))
