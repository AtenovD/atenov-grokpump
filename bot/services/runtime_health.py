from __future__ import annotations

import asyncio

from bot.services.chains import ChainAdapter
from bot.services.grok_client import breaker
from bot.services.storage import Storage


async def write_runtime_health(storage: Storage, adapters: list[ChainAdapter]) -> None:
    state = breaker.state.value
    await storage.set_runtime_health("circuit_breaker", state, float(state == "open"))
    for adapter in adapters:
        healthy = bool(adapter.price_feed_healthy)
        await storage.set_runtime_health(
            f"price_feed:{adapter.chain_id}", "healthy" if healthy else "unhealthy", float(healthy)
        )


async def run_runtime_health_reporter(
    storage: Storage, adapters: list[ChainAdapter], interval_seconds: int = 15
) -> None:
    while True:
        await write_runtime_health(storage, adapters)
        await asyncio.sleep(interval_seconds)
