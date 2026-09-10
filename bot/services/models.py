from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Token:
    mint: str
    symbol: str | None
    name: str | None
    creator: str | None
    native_in_curve: float
    unique_buyers: int | None
    created_at: float
    chain: str = "robinhood"
    reference_price: float | None = None


@dataclass
class AgentVerdict:
    name: str
    score: float  # 0.0 (reject) .. 1.0 (strong pass)
    summary: str
    flags: list[str] = field(default_factory=list)
    approve: bool = True
    fallback: bool = False  # True if this is a pessimistic fallback, not a real model answer


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    size_sol: float = 0.0


@dataclass
class TokenAnalysis:
    token: Token
    researcher: AgentVerdict | None = None
    auditor: AgentVerdict | None = None
    narrative: AgentVerdict | None = None
    timing: AgentVerdict | None = None
    checker: AgentVerdict | None = None
    total_score: float = 0.0
    risk: RiskDecision | None = None


@dataclass
class NftCollection:
    """A newly observed NFT collection on the Robinhood Chain marketplace.

    Deliberately not a `Token`: NFT collections have no bonding-curve entry
    price to dry-run buy/sell against, so this is screened and alerted on,
    never fed to `DryRunExecutor`.
    """

    address: str
    name: str | None
    symbol: str | None
    creator: str | None
    supply: int | None
    unique_minters: int | None
    created_at: float
    chain: str = "robinhood-nft"
    floor_price: float | None = None


@dataclass
class NftAnalysis:
    collection: NftCollection
    researcher: AgentVerdict | None = None
    auditor: AgentVerdict | None = None
    narrative: AgentVerdict | None = None
    timing: AgentVerdict | None = None
    total_score: float = 0.0
