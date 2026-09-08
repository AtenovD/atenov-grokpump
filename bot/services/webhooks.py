from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict
from typing import Any

import aiohttp

from bot.services.models import TokenAnalysis

logger = logging.getLogger(__name__)


def signal_payload(analysis: TokenAnalysis, emitted_at: int | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "event": "signal.passed",
        "emitted_at": int(time.time()) if emitted_at is None else emitted_at,
        "analysis": asdict(analysis),
    }


async def _post_once(
    session: aiohttp.ClientSession, url: str, payload: dict[str, Any]
) -> None:
    async with session.post(
        url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
    ) as response:
        if response.status < 200 or response.status >= 300:
            raise aiohttp.ClientResponseError(
                response.request_info, response.history,
                status=response.status, message="webhook returned non-success status",
            )


async def deliver_signal_webhooks(
    session: aiohttp.ClientSession,
    analysis: TokenAnalysis,
    urls: tuple[str, ...],
) -> None:
    if not urls:
        return
    payload = signal_payload(analysis)
    for url in urls:
        for attempt in range(2):
            try:
                await _post_once(session, url, payload)
                break
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt == 0:
                    await asyncio.sleep(0.5)
                else:
                    logger.warning("signal webhook failed after retry for %s: %s", url, exc)
