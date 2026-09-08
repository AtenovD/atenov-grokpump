from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime

import aiohttp

from bot.services.models import Token

logger = logging.getLogger(__name__)


class BaseAdapter:
    """Polls Clanker's public indexer; prices are indexed pool prices in USD."""

    chain_id = "base"

    def __init__(self, data_url: str, rpc_url: str, poll_interval: float = 5.0) -> None:
        self.data_url = data_url
        self.rpc_url = rpc_url
        self.poll_interval = poll_interval
        self._watched: set[str] = set()
        self._latest_price: dict[str, float] = {}
        self._baseline: set[str] | None = None
        self._emitted: set[str] = set()
        self.price_feed_healthy = False

    async def _fetch(self, session: aiohttp.ClientSession, limit: int = 20) -> list[dict]:
        params = {
            "chainId": "8453", "sortBy": "deployed-at", "sort": "desc",
            "limit": str(limit), "includeMarket": "true",
        }
        async with session.get(self.data_url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as response:
            response.raise_for_status()
            payload = await response.json()
        return payload.get("data", [])

    @staticmethod
    def _price(item: dict) -> float | None:
        value = item.get("priceUsd") or item.get("related", {}).get("market", {}).get("priceUsd")
        return float(value) if value and float(value) > 0 else None

    @staticmethod
    def _created_at(item: dict) -> float:
        raw = item.get("deployed_at") or item.get("created_at")
        if not raw:
            return 0.0
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()

    def _update_prices(self, items: list[dict]) -> None:
        for item in items:
            mint = item.get("contract_address")
            price = self._price(item)
            key = str(mint).lower()
            if key in self._watched and price is not None:
                self._latest_price[key] = price

    async def stream_new_tokens(self) -> AsyncIterator[Token]:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    items = await self._fetch(session)
                    self._update_prices(items)
                    addresses = {
                        str(item["contract_address"]).lower()
                        for item in items if item.get("contract_address")
                    }
                    if self._baseline is None:
                        self._baseline = addresses
                        await asyncio.sleep(self.poll_interval)
                        continue
                    for item in reversed(items):
                        mint = item.get("contract_address")
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
                            creator=item.get("msg_sender") or item.get("admin"),
                            sol_in_curve=float(item.get("starting_market_cap") or 0),
                            unique_buyers=None,
                            created_at=self._created_at(item), chain=self.chain_id,
                            reference_price=price,
                        )
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
                    logger.warning("Clanker data source failed: %s", exc)
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
                    self._update_prices(await self._fetch(session))
                    self.price_feed_healthy = True
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
                    self.price_feed_healthy = False
                    logger.warning("Clanker price refresh failed: %s", exc)
                await asyncio.sleep(self.poll_interval)
