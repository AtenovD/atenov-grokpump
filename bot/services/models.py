from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Token:
    mint: str
    symbol: str | None
    name: str | None
    creator: str | None
    sol_in_curve: float
    unique_buyers: int
    created_at: float


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
    auditor: AgentVerdict | None = None
    narrative: AgentVerdict | None = None
    timing: AgentVerdict | None = None
    checker: AgentVerdict | None = None
    total_score: float = 0.0
    risk: RiskDecision | None = None
