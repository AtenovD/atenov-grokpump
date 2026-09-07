from __future__ import annotations

import asyncio
import json
import logging
import time

import websockets

from bot.config import config

logger = logging.getLogger(__name__)


class PriceFeed:
    """Tracks the live bonding-curve price of a dynamic set of mints via PumpPortal's
    per-token trade stream. Positions are added/removed as they open/close; the
    background loop re-subscribes whenever the watch list changes.

    This replaces random simulated exits: every price used to close a dry-run
    position comes from a real trade observed on the actual bonding curve.
    """

    def __init__(self) -> None:
        self._latest_price: dict[str, float] = {}
        self._last_update: dict[str, float] = {}
        self._watched: set[str] = set()
        self._want_resubscribe = asyncio.Event()

    def watch(self, mint: str) -> None:
        if mint not in self._watched:
            self._watched.add(mint)
            self._want_resubscribe.set()

    def unwatch(self, mint: str) -> None:
        self._watched.discard(mint)
        self._latest_price.pop(mint, None)
        self._last_update.pop(mint, None)
        self._want_resubscribe.set()

    def get_price(self, mint: str) -> float | None:
        return self._latest_price.get(mint)

    def age_seconds(self, mint: str) -> float | None:
        ts = self._last_update.get(mint)
        return None if ts is None else time.time() - ts

    async def run(self) -> None:
        """Long-running loop: connect, subscribe to whatever's currently watched,
        and reconnect (picking up the current watch list) whenever the socket drops
        or the watch list changes underneath it."""
        while True:
            try:
                async with websockets.connect(config.data_ws_url, ping_interval=20) as ws:
                    await self._subscribe_current(ws)
                    self._want_resubscribe.clear()
                    logger.info("price feed connected, watching %d mint(s)", len(self._watched))

                    consumer = asyncio.create_task(self._consume(ws))
                    resub_wait = asyncio.create_task(self._want_resubscribe.wait())
                    done, pending = await asyncio.wait(
                        {consumer, resub_wait}, return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in pending:
                        task.cancel()
                    if resub_wait in done:
                        await self._subscribe_current(ws)
                        self._want_resubscribe.clear()
                        await consumer  # let it keep consuming on the same connection
            except (websockets.exceptions.WebSocketException, OSError) as exc:
                logger.warning("price feed connection dropped: %s — reconnecting in 5s", exc)
                await asyncio.sleep(5)

    async def _subscribe_current(self, ws) -> None:
        if self._watched:
            await ws.send(json.dumps({"method": "subscribeTokenTrade", "keys": list(self._watched)}))

    async def _consume(self, ws) -> None:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            mint = data.get("mint")
            if not mint or mint not in self._watched:
                continue
            price = self._price_from_trade(data)
            if price is not None:
                self._latest_price[mint] = price
                self._last_update[mint] = time.time()

    @staticmethod
    def _price_from_trade(data: dict) -> float | None:
        sol_reserves = data.get("vSolInBondingCurve")
        token_reserves = data.get("vTokensInBondingCurve")
        if sol_reserves is not None and token_reserves and float(token_reserves) > 0:
            return float(sol_reserves) / float(token_reserves)
        return None
