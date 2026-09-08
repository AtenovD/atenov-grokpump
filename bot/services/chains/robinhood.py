from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

import aiohttp

from bot.services.models import Token

logger = logging.getLogger(__name__)


class RobinhoodAdapter:
    """Polls hood.fun's public board indexer and uses its exact curve/pool price."""

    chain_id = "robinhood"

    def __init__(self, data_url: str, rpc_url: str, poll_interval: float = 5.0) -> None:
        self.data_url = data_url.rstrip("/")
        self.rpc_url = rpc_url
        self.poll_interval = poll_interval
        self._watched: set[str] = set()
        self._latest_price: dict[str, float] = {}
        self._baseline: set[str] | None = None
        self._emitted: set[str] = set()
        self.price_feed_healthy = False

    async def _fetch(self, session: aiohttp.ClientSession) -> dict:
        async with session.get(
            f"{self.data_url}/api/board", timeout=aiohttp.ClientTimeout(total=20)
        ) as response:
            response.raise_for_status()
            return await response.json()

    @staticmethod
    def _price(token: dict) -> float | None:
        pair_price = token.get("pairPriceWei")
        if pair_price and int(pair_price) > 0:
            return int(pair_price) / 10**18
        curve = token.get("curve") or {}
        virtual_eth = int(curve.get("virtualEth") or 0)
        virtual_tokens = int(curve.get("virtualTokens") or 0)
        if virtual_eth > 0 and virtual_tokens > 0:
            return virtual_eth / virtual_tokens
        return None

    def _update_prices(self, tokens: list[dict]) -> None:
        for token in tokens:
            mint = token.get("address")
            price = self._price(token)
            key = str(mint).lower()
            if key in self._watched and price is not None:
                self._latest_price[key] = price

    async def stream_new_tokens(self) -> AsyncIterator[Token]:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    payload = await self._fetch(session)
                    tokens = payload.get("tokens", [])
                    self._update_prices(tokens)
                    addresses = {
                        str(item["address"]).lower() for item in tokens if item.get("address")
                    }
                    if self._baseline is None:
                        self._baseline = addresses
                        await asyncio.sleep(self.poll_interval)
                        continue
                    for item in reversed(tokens):
                        mint = item.get("address")
                        price = self._price(item)
                        key = str(mint).lower()
                        if (
                            not mint or key in self._baseline or key in self._emitted
                            or price is None
                        ):
                            continue
                        self._emitted.add(key)
                        yield Token(
                            mint=mint, symbol=item.get("symbol"), name=item.get("name"),
                            creator=item.get("creator"), sol_in_curve=float((item.get("curve") or {}).get("realEth") or 0) / 10**18,
                            unique_buyers=None,
                            created_at=float(item.get("timestamp") or 0), chain=self.chain_id,
                            reference_price=price,
                        )
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError) as exc:
                    logger.warning("hood.fun data source failed: %s", exc)
                await asyncio.sleep(self.poll_interval)

    def watch(self, mint: str) -> None:
        self._watched.add(mint.lower())

    def unwatch(self, mint: str) -> None:
        self._watched.discard(mint.lower())
        self._latest_price.pop(mint.lower(), None)

    def get_price(self, mint: str) -> float | None:
        return self._latest_price.get(mint.lower())

    async def run(self) -> None:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    payload = await self._fetch(session)
                    self._update_prices(payload.get("tokens", []))
                    self.price_feed_healthy = True
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError) as exc:
                    self.price_feed_healthy = False
                    logger.warning("hood.fun price refresh failed: %s", exc)
                await asyncio.sleep(self.poll_interval)
