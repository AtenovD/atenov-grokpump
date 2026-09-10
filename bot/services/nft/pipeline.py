from __future__ import annotations

import time

import aiohttp
from aiogram import Bot

from bot.config import config
from bot.services.chains import chain_label
from bot.services.cross_signal import cross_surface_note
from bot.services.models import AgentVerdict, NftAnalysis, NftCollection
from bot.services.nft import agents as nft_agents
from bot.services.nft.models import collection_url
from bot.services.reputation import ReputationBook
from bot.services.storage import Storage

NFT_CHAIN = "robinhood-nft"

# Below this many unique minters, or younger than this, a collection is
# filtered out before it costs a single Grok call - same idea as the token
# pipeline's code-only pre-filter.


def _code_filter(collection: NftCollection) -> str | None:
    if collection.unique_minters is not None and collection.unique_minters < config.nft_min_unique_minters:
        return "too_few_minters"
    if time.time() - collection.created_at < config.nft_min_launch_age_seconds:
        return "too_young"
    return None


async def _researcher_note(storage: Storage, collection: NftCollection) -> AgentVerdict:
    """Free DB-only pre-check: creator reputation on the NFT surface, plus the
    cross-surface signal (same address already running a token on Robinhood)."""
    flags: list[str] = []
    notes: list[str] = []

    if collection.creator:
        rugs, wins = await storage.creator_stats(collection.creator, NFT_CHAIN)
        if rugs:
            flags.append("creator_has_prior_rugs")
            notes.append(f"creator has {rugs} prior rug(s) and {wins} prior win(s) on Robinhood NFT")
        elif wins:
            notes.append(f"creator has {wins} prior clean exit(s) on Robinhood NFT, no rugs on record")

    cross_note = await cross_surface_note(storage, collection.creator, NFT_CHAIN)
    if cross_note:
        flags.append("cross_surface_creator")
        notes.append(cross_note)

    approve = "creator_has_prior_rugs" not in flags
    return AgentVerdict(
        name="nft_researcher",
        score=0.3 if flags else 0.8,
        summary="; ".join(notes) if notes else "no prior history for this creator",
        flags=flags,
        approve=approve,
    )


async def screen_collection(
    session: aiohttp.ClientSession,
    storage: Storage,
    reputation: ReputationBook,
    collection: NftCollection,
) -> NftAnalysis | None:
    """Screens one NFT collection. Alert-only: there is no dry-run buy/sell for
    an NFT collection the way there is for a bonding-curve token, so a pass
    here produces a Telegram alert and a signal-log row, nothing else."""
    analysis = NftAnalysis(collection=collection)

    reason = _code_filter(collection)
    if reason:
        await storage.log_signal(collection.address, collection.symbol, None, "filter", "skip", reason, NFT_CHAIN)
        return None

    blocked = await reputation.is_blocked(collection.creator, NFT_CHAIN)
    if blocked:
        await storage.log_signal(collection.address, collection.symbol, None, "reputation", "skip", blocked, NFT_CHAIN)
        return None

    analysis.researcher = await _researcher_note(storage, collection)
    analysis.auditor = await nft_agents.run_nft_auditor(session, collection)
    analysis.narrative = await nft_agents.run_nft_narrative(session, collection)

    weights = {"auditor": 0.55, "narrative": 0.45}
    total = analysis.auditor.score * weights["auditor"] + analysis.narrative.score * weights["narrative"]
    analysis.total_score = round(total, 4)

    if total < 0.5 or not (analysis.auditor.approve and analysis.narrative.approve):
        await storage.log_signal(
            collection.address, collection.symbol, total, "scoring", "skip", "below_threshold", NFT_CHAIN
        )
        return None

    await storage.log_signal(collection.address, collection.symbol, total, "nft_screen", "passed", "", NFT_CHAIN)
    return analysis


async def broadcast_nft_signal(bot: Bot, analysis: NftAnalysis) -> None:
    if not config.nft_alert_chat_id:
        return
    collection = analysis.collection
    parts = [f"{v.name}: {v.summary}" for v in (analysis.auditor, analysis.narrative) if v]
    text = (
        f"🖼️ <b>{collection.symbol or collection.address[:8]}</b> - NFT score {analysis.total_score:.2f}\n"
        f"{chain_label(NFT_CHAIN)}\n\n"
        f"{' | '.join(parts)}\n\n"
        f"{collection_url(collection.address)}"
    )
    await bot.send_message(config.nft_alert_chat_id, text, disable_web_page_preview=True)
