from __future__ import annotations

import time
from dataclasses import dataclass

from bot.services.models import Token


@dataclass
class TradeResult:
    ok: bool
    price: float = 0.0
    tx_hash: str = ""
    error: str = ""


class DryRunExecutor:
    """Simulates a buy/sell — no wallet, no signing, no network call to any chain.

    This is intentionally the only executor in this project. A live executor
    that signs and broadcasts real Solana transactions is a materially
    different, much higher-stakes piece of software and is out of scope here
    on purpose — this bot is a research/screening tool, not a trading bot.

    Exit prices are supplied by the caller (from PriceFeed, tracking the real
    bonding curve) — this executor never invents a price itself.
    """

    async def buy(self, token: Token, size_sol: float) -> TradeResult:
        price = token.reference_price
        if price is None:
            # Preserve the existing pump.fun dry-run entry calculation.
            price = max(token.sol_in_curve, 0.0001) / max(token.unique_buyers or 1, 1)
        return TradeResult(ok=True, price=price, tx_hash=f"dryrun-buy-{token.mint[:8]}-{int(time.time())}")

    async def sell(self, mint: str, exit_price: float) -> TradeResult:
        return TradeResult(ok=True, price=exit_price, tx_hash=f"dryrun-sell-{mint[:8]}-{int(time.time())}")
