from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from bot.services.models import Token

CHAIN_LABELS = {
    "solana": "🟣 Solana",
    "base": "🔵 Base",
    "robinhood": "🟢 Robinhood",
}


class ChainAdapter(Protocol):
    chain_id: str

    def stream_new_tokens(self) -> AsyncIterator[Token]: ...
    def watch(self, mint: str) -> None: ...
    def unwatch(self, mint: str) -> None: ...
    def get_price(self, mint: str) -> float | None: ...
    async def run(self) -> None: ...


def chain_label(chain: str) -> str:
    return CHAIN_LABELS.get(chain, chain.title())


def token_url(chain: str, mint: str) -> str:
    if chain == "solana":
        return f"https://pump.fun/{mint}"
    if chain == "base":
        return f"https://clanker.world/clanker/{mint}"
    return f"https://hood.fun/coin/{mint}"


def build_adapters() -> list[ChainAdapter]:
    from bot.config import config
    from bot.services.chains.base import BaseAdapter
    from bot.services.chains.robinhood import RobinhoodAdapter
    from bot.services.chains.solana import SolanaAdapter

    factories = {
        "solana": lambda: SolanaAdapter(config.data_ws_url),
        "base": lambda: BaseAdapter(config.base_data_url, config.base_rpc_url),
        "robinhood": lambda: RobinhoodAdapter(config.robinhood_data_url, config.robinhood_rpc_url),
    }
    unknown = set(config.enabled_chains) - factories.keys()
    if unknown:
        raise ValueError(f"unsupported chain(s) in ENABLED_CHAINS: {', '.join(sorted(unknown))}")
    return [factories[chain]() for chain in config.enabled_chains]
