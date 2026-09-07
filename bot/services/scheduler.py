from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import deque

import aiohttp
from aiogram import Bot

from bot.services import pipeline
from bot.services.executor import DryRunExecutor
from bot.services.monitor import stream_new_tokens
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


async def run_monitor_loop(bot: Bot, storage: Storage) -> None:
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
            await storage.mark_seen(token.mint)

            try:
                analysis = await pipeline.screen_token(
                    session, storage, risk, reputation, executor, token, pulse.snapshot()
                )
            except Exception:
                logger.exception("screening %s crashed", token.mint)
                continue

            if analysis is not None:
                await pipeline.broadcast_signal(bot, analysis)


async def run_position_watcher(storage: Storage, reputation: ReputationBook, check_interval_sec: int = 60) -> None:
    """Periodically 'closes' dry-run positions with a simulated outcome, feeding the
    reputation book and daily PnL — since there's no live price feed to watch."""
    executor = DryRunExecutor()
    while True:
        await asyncio.sleep(check_interval_sec)
        for position in await storage.open_positions():
            if time.time() - position.opened_at < 300:
                continue  # give a position at least 5 minutes before simulating an exit
            result = await executor.sell(position.mint, position.entry_price)
            pnl_sol = (result.price - position.entry_price) / position.entry_price * position.sol_spent
            pnl_pct = (result.price - position.entry_price) / position.entry_price * 100
            await storage.close_position(position.mint)
            await storage.record_pnl_only(pnl_sol)
            await reputation.record_outcome(position.creator, pnl_pct)
