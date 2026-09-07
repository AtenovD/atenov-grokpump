from __future__ import annotations

import json

import aiohttp

from bot.config import config
from bot.services.grok_client import ask_grok
from bot.services.models import AgentVerdict, Token

# Each agent is one prompt + one JSON contract. On any failure the caller gets
# a pessimistic AgentVerdict (score 0, approve=False) — a broken check must
# never silently let a token through.

_AUDITOR_PROMPT = """You are a fraud auditor reviewing a brand-new Solana memecoin on pump.fun.
You will receive trade and holder statistics. Look for signs of wash trading, bundled buys from
related wallets, or a holder distribution concentrated in a handful of addresses.
Reply with ONLY a JSON object: {"score": 0.0-1.0, "summary": "...", "flags": ["..."], "approve": true|false}.
score is your confidence this activity is organic (1.0 = clean, 0.0 = clearly manipulated)."""

_NARRATIVE_PROMPT = """You are evaluating the meme/narrative strength of a brand-new Solana memecoin
on pump.fun, based only on its name, symbol and any description text provided.
Reply with ONLY a JSON object: {"score": 0.0-1.0, "summary": "...", "flags": ["..."], "approve": true|false}.
score is how likely this specific meme is to catch attention (1.0 = strong, 0.0 = generic/derivative)."""

_TIMING_PROMPT = """You are assessing whether current market conditions favor entering a new pump.fun
launch right now, based on the observed launch rate, survival rate and recent outcome statistics you
are given (all self-measured by this system, not external market data).
Reply with ONLY a JSON object: {"score": 0.0-1.0, "summary": "...", "flags": ["..."], "approve": true|false}.
score is how favorable the current window looks (1.0 = favorable, 0.0 = avoid entries right now)."""

_CHECKER_PROMPT = """You are the final adversarial reviewer before a trade is placed. You will receive
the token's data plus the verdicts of three other agents (auditor, narrative, timing). Your job is
specifically to look for reasons to REJECT — argue against the token even if the other three passed it.
Reply with ONLY a JSON object: {"score": 0.0-1.0, "summary": "...", "flags": ["..."], "approve": true|false}.
approve=false if you find a credible reason this token should not be bought."""


def _fallback(name: str, reason: str) -> AgentVerdict:
    return AgentVerdict(name=name, score=0.0, summary=f"fallback: {reason}", approve=False, fallback=True)


def _parse(name: str, data: dict | None, reason_if_none: str) -> AgentVerdict:
    if data is None:
        return _fallback(name, reason_if_none)
    try:
        return AgentVerdict(
            name=name,
            score=float(data.get("score", 0.0)),
            summary=str(data.get("summary", "")),
            flags=list(data.get("flags", [])),
            approve=bool(data.get("approve", False)),
        )
    except (TypeError, ValueError) as exc:
        return _fallback(name, f"malformed response: {exc}")


async def run_auditor(session: aiohttp.ClientSession, token: Token, holders: dict, trades: dict) -> AgentVerdict:
    message = json.dumps({"token": token.__dict__, "holders": holders, "trades": trades}, default=str)
    data = await ask_grok(session, _AUDITOR_PROMPT, message, model=config.grok_fast_model)
    return _parse("auditor", data, "grok call failed")


async def run_narrative(session: aiohttp.ClientSession, token: Token) -> AgentVerdict:
    message = json.dumps({"symbol": token.symbol, "name": token.name}, default=str)
    data = await ask_grok(session, _NARRATIVE_PROMPT, message, model=config.grok_fast_model)
    return _parse("narrative", data, "grok call failed")


async def run_timing(session: aiohttp.ClientSession, market_snapshot: dict) -> AgentVerdict:
    message = json.dumps(market_snapshot, default=str)
    data = await ask_grok(session, _TIMING_PROMPT, message, model=config.grok_fast_model)
    return _parse("timing", data, "grok call failed")


async def run_checker(session: aiohttp.ClientSession, token: Token, prior: list[AgentVerdict]) -> AgentVerdict:
    message = json.dumps(
        {
            "token": token.__dict__,
            "prior_verdicts": [v.__dict__ for v in prior],
        },
        default=str,
    )
    data = await ask_grok(session, _CHECKER_PROMPT, message, model=config.grok_checker_model)
    return _parse("checker", data, "grok call failed")
