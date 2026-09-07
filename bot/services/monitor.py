from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator

import websockets

from bot.config import config
from bot.services.models import Token

logger = logging.getLogger(__name__)

_SUBSCRIBE_PAYLOAD = json.dumps({"method": "subscribeNewToken"})


def _parse_new_token_event(raw: dict) -> Token | None:
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
    )


async def stream_new_tokens() -> AsyncIterator[Token]:
    """Connects to the public pump.fun launch feed and yields new tokens as they appear.

    Reconnects automatically on any drop — a single dead socket must not take
    the whole monitoring loop down for the rest of the day.
    """
    while True:
        try:
            async with websockets.connect(config.data_ws_url, ping_interval=20) as ws:
                await ws.send(_SUBSCRIBE_PAYLOAD)
                logger.info("connected to launch feed at %s", config.data_ws_url)
                async for raw_message in ws:
                    try:
                        data = json.loads(raw_message)
                    except json.JSONDecodeError:
                        continue
                    token = _parse_new_token_event(data)
                    if token is not None:
                        yield token
        except (websockets.exceptions.WebSocketException, OSError) as exc:
            logger.warning("launch feed connection dropped: %s — reconnecting in 5s", exc)
            import asyncio

            await asyncio.sleep(5)
