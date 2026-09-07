from __future__ import annotations

import asyncio
import logging
import time
from collections import deque

import aiohttp
from aiogram import Bot

from bot.config import config
from bot.services import pipeline
from bot.services.executor import DryRunExecutor
from bot.services.monitor import stream_new_tokens
from bot.services.price_feed import PriceFeed
from bot.services.reputation import ReputationBook
from bot.services.risk import RiskManager
from bot.services.storage import Storage

logger = logging.getLogger(__name__)

# How many recent launches/outcomes the timing agent's market snapshot is built from.
_WINDOW_SECONDS = 900.0
_OUTCOME_MEMORY = 50


class MarketPulse:
    """Rolling window of what this process has actually observed — no external
    price feeds, so the timing agent only ever judges its own vantage point."""

    def __init__(self) -> None:
        self._launches: deque[float] = deque()
        self._outcomes: deque[float] = deque(maxlen=_OUTCOME_MEMORY)

    def record_launch(self) -> None:
        now = time.time()
        self._launches.append(now)
        cutoff = now - _WINDOW_SECONDS
        while self._launches and self._launches[0] < cutoff:
            self._launches.popleft()

    def record_outcome(self, pnl_pct: float) -> None:
        self._outcomes.append(pnl_pct)

    def snapshot(self) -> dict:
        minutes = _WINDOW_SECONDS / 60.0
        data = {
            "launches_per_minute": round(len(self._launches) / minutes, 2) if minutes else 0.0,
            "window_minutes": minutes,
        }
        if self._outcomes:
            wins = [p for p in self._outcomes if p > 0]
            data["win_rate"] = round(len(wins) / len(self._outcomes), 3)
            data["sample_size"] = len(self._outcomes)
        return data


async def run_monitor_loop(bot: Bot, storage: Storage, price_feed: PriceFeed) -> None:
    """Consumes the launch feed, screens each token, opens dry-run positions."""
    pulse = MarketPulse()
    risk = RiskManager(storage)
    reputation = ReputationBook(storage)
    executor = DryRunExecutor()

    async with aiohttp.ClientSession() as session:
        async for token in stream_new_tokens():
            pulse.record_launch()
            if await storage.is_seen(token.mint):
                continue
            await storage.mark_seen(token.mint, token.symbol, token.name)

            try:
                analysis = await pipeline.screen_token(
                    session, storage, risk, reputation, executor, token, pulse.snapshot()
                )
            except Exception:
                logger.exception("screening %s crashed", token.mint)
                continue

            if analysis is not None:
                price_feed.watch(token.mint)
                await pipeline.broadcast_signal(bot, session, analysis)


async def run_position_watcher(
    storage: Storage, reputation: ReputationBook, price_feed: PriceFeed, check_interval_sec: int = 15
) -> None:
    """Watches real bonding-curve prices for open positions and force-closes any
    position whose drawdown from entry hits STOP_LOSS_PCT — exactly the exit rule
    a live executor would need, run here against a real (but unexecuted) price."""
    executor = DryRunExecutor()

    # Positions may already be open from a previous run (state persists in sqlite) —
    # make sure the price feed is watching all of them, not just newly opened ones.
    for position in await storage.open_positions():
        price_feed.watch(position.mint)

    while True:
        await asyncio.sleep(check_interval_sec)
        for position in await storage.open_positions():
            price = price_feed.get_price(position.mint)
            if price is None:
                continue  # no trade observed yet for this mint — nothing to act on

            drawdown_pct = (position.entry_price - price) / position.entry_price * 100
            if drawdown_pct < config.stop_loss_pct:
                continue  # still within tolerance, keep watching

            result = await executor.sell(position.mint, price)
            pnl_sol = (result.price - position.entry_price) / position.entry_price * position.sol_spent
            pnl_pct = (result.price - position.entry_price) / position.entry_price * 100

            await storage.close_position(position.mint, price, "stop_loss")
            await storage.record_pnl_only(pnl_sol)
            await reputation.record_outcome(position.creator, pnl_pct)
            price_feed.unwatch(position.mint)
            logger.info(
                "stop-loss closed %s: entry=%.10f exit=%.10f pnl=%.4f SOL (%.1f%%)",
                position.mint[:8], position.entry_price, price, pnl_sol, pnl_pct,
            )
