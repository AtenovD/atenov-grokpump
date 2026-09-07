from __future__ import annotations

import json

import aiohttp

from bot.config import config
from bot.services.grok_client import ask_grok
from bot.services.models import TokenAnalysis

_DIGEST_PROMPT = """You write a single short paragraph (2-4 sentences) explaining, in plain language,
why a token passed or failed a screening pipeline, based on the four agent verdicts you're given.
Do not repeat all four verdicts verbatim — synthesize the actual reasoning into something a person
could read in five seconds. Mention the one or two factors that mattered most.
Reply with ONLY a JSON object: {"digest": "..."}."""


def _fallback_digest(analysis: TokenAnalysis) -> str:
    """Used if the synthesis call fails — falls back to the raw per-agent summaries
    rather than showing nothing."""
    parts = []
    for verdict in (analysis.auditor, analysis.narrative, analysis.timing, analysis.checker):
        if verdict:
            parts.append(f"{verdict.name}: {verdict.summary}")
    return " | ".join(parts)


async def synthesize_digest(session: aiohttp.ClientSession, analysis: TokenAnalysis) -> str:
    verdicts = {
        v.name: {"score": v.score, "summary": v.summary, "flags": v.flags, "approve": v.approve}
        for v in (analysis.auditor, analysis.narrative, analysis.timing, analysis.checker)
        if v is not None
    }
    message = json.dumps({"total_score": analysis.total_score, "verdicts": verdicts}, default=str)
    data = await ask_grok(session, _DIGEST_PROMPT, message, model=config.grok_fast_model)
    if data and isinstance(data.get("digest"), str) and data["digest"].strip():
        return data["digest"].strip()
    return _fallback_digest(analysis)
