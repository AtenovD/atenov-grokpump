from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator

import websockets

from bot.services.models import Token

logger = logging.getLogger(__name__)


class SolanaAdapter:
    chain_id = "solana"
    _NEW_TOKEN_PAYLOAD = json.dumps({"method": "subscribeNewToken"})

    def __init__(self, data_url: str) -> None:
        self.data_url = data_url
        self._latest_price: dict[str, float] = {}
        self._last_update: dict[str, float] = {}
        self._watched: set[str] = set()
        self._want_resubscribe = asyncio.Event()
        self.price_feed_healthy = False

    @staticmethod
    def parse_new_token(raw: dict) -> Token | None:
        mint = raw.get("mint")
        if not mint:
            return None
        return Token(
            mint=mint,
            symbol=raw.get("symbol"),
            name=raw.get("name"),
            creator=raw.get("traderPublicKey") or raw.get("creator"),
            sol_in_curve=float(raw.get("vSolInBondingCurve") or raw.get("solAmount") or 0.0),
            unique_buyers=int(raw.get("uniqueBuyers") or 1),
            created_at=time.time(),
            chain=self.chain_id,
        )

    async def stream_new_tokens(self) -> AsyncIterator[Token]:
        while True:
            try:
                async with websockets.connect(self.data_url, ping_interval=20) as ws:
                    self.price_feed_healthy = True
                    await ws.send(self._NEW_TOKEN_PAYLOAD)
                    logger.info("connected to Solana launch feed at %s", self.data_url)
                    async for raw_message in ws:
                        try:
                            data = json.loads(raw_message)
                        except json.JSONDecodeError:
                            continue
                        token = self.parse_new_token(data)
                        if token is not None:
                            yield token
            except (websockets.exceptions.WebSocketException, OSError) as exc:
                logger.warning("Solana launch feed dropped: %s; reconnecting in 5s", exc)
                await asyncio.sleep(5)

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

    async def run(self) -> None:
        while True:
            try:
                async with websockets.connect(self.data_url, ping_interval=20) as ws:
                    if self._watched:
                        await ws.send(json.dumps({"method": "subscribeTokenTrade", "keys": list(self._watched)}))
                    self._want_resubscribe.clear()
                    consumer = asyncio.create_task(self._consume(ws))
                    changed = asyncio.create_task(self._want_resubscribe.wait())
                    done, pending = await asyncio.wait(
                        {consumer, changed}, return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                    for task in done:
                        if task is consumer:
                            task.result()
            except (websockets.exceptions.WebSocketException, OSError) as exc:
                self.price_feed_healthy = False
                logger.warning("Solana price feed dropped: %s; reconnecting in 5s", exc)
                await asyncio.sleep(5)

    async def _consume(self, ws) -> None:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            mint = data.get("mint")
            if not mint or mint not in self._watched:
                continue
            price = self.price_from_trade(data)
            if price is not None:
                self._latest_price[mint] = price
                self._last_update[mint] = time.time()

    @staticmethod
    def price_from_trade(data: dict) -> float | None:
        sol_reserves = data.get("vSolInBondingCurve")
        token_reserves = data.get("vTokensInBondingCurve")
        if sol_reserves is not None and token_reserves and float(token_reserves) > 0:
            return float(sol_reserves) / float(token_reserves)
        return None
