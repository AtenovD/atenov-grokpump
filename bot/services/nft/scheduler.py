from __future__ import annotations

import asyncio
import logging

import aiohttp
from aiogram import Bot

from bot.config import config
from bot.services.chains import chain_label
from bot.services.nft import pipeline
from bot.services.nft.adapter import RobinhoodNftAdapter
from bot.services.nft.models import collection_url
from bot.services.reputation import ReputationBook
from bot.services.storage import Storage

logger = logging.getLogger(__name__)

NFT_CHAIN = "robinhood-nft"


async def run_nft_monitor_loop(bot: Bot, storage: Storage, adapter: RobinhoodNftAdapter) -> None:
    """Discovers new NFT collections and runs them through the screening pipeline -
    the NFT-side counterpart to `bot.services.scheduler.run_monitor_loop`."""
    reputation = ReputationBook(storage)

    async with aiohttp.ClientSession() as session:
        async for collection in adapter.stream_new_collections():
            if await storage.is_seen(collection.address, NFT_CHAIN):
                continue
            await storage.mark_seen(
                collection.address, collection.symbol, collection.name, NFT_CHAIN, collection.creator
            )

            try:
                analysis = await pipeline.screen_collection(session, storage, reputation, collection)
            except Exception:
                logger.exception("NFT screening %s crashed", collection.address)
                continue

            if analysis is not None:
                adapter.watch(collection.address)
                await pipeline.broadcast_nft_signal(bot, analysis)


async def run_floor_sweep_watcher(
    bot: Bot, storage: Storage, adapter: RobinhoodNftAdapter, check_interval_sec: int = 30
) -> None:
    """Watches every collection the monitor loop started watching for a sudden
    floor-price move, in either direction, away from the first floor price this
    process observed for it - the NFT-side counterpart to the token pipeline's
    real-price stop-loss, but alert-only (there is no dry-run position to close)."""
    baseline: dict[str, float] = {}
    alerted: set[str] = set()

    while True:
        await asyncio.sleep(check_interval_sec)
        for address in adapter.watched_addresses():
            floor = adapter.get_floor_price(address)
            if floor is None:
                continue
            await storage.record_price_snapshot(address, floor, NFT_CHAIN)

            if address not in baseline:
                baseline[address] = floor
                continue

            start = baseline[address]
            change_pct = (floor - start) / start * 100 if start else 0.0
            if address in alerted:
                continue

            if change_pct <= -config.floor_sweep_drop_pct:
                await _alert_floor_sweep(bot, address, start, floor, change_pct, "drop")
                alerted.add(address)
            elif change_pct >= config.floor_sweep_pump_pct:
                await _alert_floor_sweep(bot, address, start, floor, change_pct, "pump")
                alerted.add(address)


async def _alert_floor_sweep(
    bot: Bot, address: str, start: float, current: float, change_pct: float, kind: str
) -> None:
    if not config.nft_alert_chat_id:
        return
    icon = "🔴" if kind == "drop" else "🟢"
    label = "possible rug (floor collapsed)" if kind == "drop" else "possible breakout (floor pumping)"
    text = (
        f"{icon} <b>Floor sweep</b> - {label}\n"
        f"{chain_label(NFT_CHAIN)}\n\n"
        f"Floor moved {change_pct:+.1f}% ({start:.6f} -> {current:.6f} ETH)\n"
        f"{collection_url(address)}"
    )
    await bot.send_message(config.nft_alert_chat_id, text, disable_web_page_preview=True)
