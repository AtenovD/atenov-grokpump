from __future__ import annotations

from bot.config import config
from bot.services.chains.solana import SolanaAdapter


class PriceFeed(SolanaAdapter):
    """Backward-compatible name for the Solana price adapter."""

    def __init__(self) -> None:
        super().__init__(config.data_ws_url)

    _price_from_trade = staticmethod(SolanaAdapter.price_from_trade)
