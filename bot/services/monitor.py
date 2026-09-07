from __future__ import annotations

from collections.abc import AsyncIterator

from bot.config import config
from bot.services.chains.solana import SolanaAdapter
from bot.services.models import Token


def _parse_new_token_event(raw: dict) -> Token | None:
    """Compatibility shim for existing imports and manual tests."""
    return SolanaAdapter.parse_new_token(raw)


async def stream_new_tokens() -> AsyncIterator[Token]:
    """Connects to the public pump.fun launch feed and yields new tokens as they appear.

    Reconnects automatically on any drop — a single dead socket must not take
    the whole monitoring loop down for the rest of the day.
    """
    adapter = SolanaAdapter(config.data_ws_url)
    async for token in adapter.stream_new_tokens():
        yield token
