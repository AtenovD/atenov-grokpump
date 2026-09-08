from __future__ import annotations

import logging
import json
import time
from dataclasses import asdict

import aiohttp
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import config
from bot.services.chains import chain_label, token_url
from bot.services import agents
from bot.services.digest import synthesize_digest
from bot.services.executor import DryRunExecutor
from bot.services.models import Token, TokenAnalysis
from bot.services.reputation import ReputationBook
from bot.services.risk import RiskManager
from bot.services.storage import Position, Storage
from bot.services.webhooks import deliver_signal_webhooks

logger = logging.getLogger(__name__)

# Below this many unique buyers, or younger than this, a launch is filtered
# out before it costs a single Grok call.
CODE_FILTER_MIN_BUYERS = 5


def _code_filter(token: Token) -> str | None:
    if token.unique_buyers is not None and token.unique_buyers < config.min_unique_buyers:
        return "too_few_buyers"
    if time.time() - token.created_at < config.min_launch_age_seconds:
        return "too_young"
    return None


async def screen_token(
    session: aiohttp.ClientSession,
    storage: Storage,
    risk: RiskManager,
    reputation: ReputationBook,
    executor: DryRunExecutor,
    token: Token,
    market_snapshot: dict,
) -> TokenAnalysis | None:
    """Runs one token through the full pipeline. Returns the analysis if it was bought (dry-run)."""
    analysis = TokenAnalysis(token=token)

    reason = _code_filter(token)
    if reason:
        await storage.log_signal(token.mint, token.symbol, None, "filter", "skip", reason, token.chain)
        return None

    blocked = await reputation.is_blocked(token.creator, token.chain)
    if blocked:
        await storage.log_signal(token.mint, token.symbol, None, "reputation", "skip", blocked, token.chain)
        return None

    # Researcher is a free, instant DB lookup (creator history, copycat-name detection) —
    # it runs before any paid Grok call and its findings are handed to the checker later.
    analysis.researcher = await agents.run_researcher(storage, token)

    # Auditor and narrative can run independently; timing needs the shared snapshot.
    analysis.auditor = await agents.run_auditor(session, token, holders={}, trades={})
    analysis.narrative = await agents.run_narrative(session, token)
    analysis.timing = await agents.run_timing(session, market_snapshot)

    weights = {"auditor": 0.4, "narrative": 0.3, "timing": 0.3}
    total = (
        analysis.auditor.score * weights["auditor"]
        + analysis.narrative.score * weights["narrative"]
        + analysis.timing.score * weights["timing"]
    )
    analysis.total_score = round(total, 4)

    if total < 0.5 or not (analysis.auditor.approve and analysis.narrative.approve and analysis.timing.approve):
        await storage.log_signal(
            token.mint, token.symbol, total, "scoring", "skip", "below_threshold", token.chain
        )
        return None

    analysis.checker = await agents.run_checker(
        session, token, [analysis.researcher, analysis.auditor, analysis.narrative, analysis.timing]
    )
    if not analysis.checker.approve:
        await storage.log_signal(
            token.mint, token.symbol, total, "checker", "skip", analysis.checker.summary, token.chain
        )
        return None

    analysis.risk = await risk.evaluate(total)
    if not analysis.risk.approved:
        await storage.log_signal(
            token.mint, token.symbol, total, "risk", "skip", analysis.risk.reason, token.chain
        )
        return None

    result = await executor.buy(token, analysis.risk.size_sol)
    if not result.ok:
        await storage.log_signal(
            token.mint, token.symbol, total, "executor", "skip", result.error, token.chain
        )
        return None

    await storage.open_position(
        Position(
            mint=token.mint,
            symbol=token.symbol,
            entry_price=result.price,
            sol_spent=analysis.risk.size_sol,
            score=total,
            creator=token.creator,
            opened_at=int(time.time()),
            status="open",
            chain=token.chain,
        )
    )
    await storage.record_trade()
    await storage.log_signal(
        token.mint, token.symbol, total, "executor", "bought", result.tx_hash, token.chain
    )
    return analysis


async def broadcast_signal(
    bot: Bot, session: aiohttp.ClientSession, storage: Storage, analysis: TokenAnalysis
) -> None:
    await deliver_signal_webhooks(session, analysis, config.webhook_urls)
    if not config.alert_chat_id:
        return
    token = analysis.token
    digest = await synthesize_digest(session, analysis)
    text = (
        f"🟢 <b>{token.symbol or token.mint[:8]}</b> — score {analysis.total_score:.2f}\n"
        f"{chain_label(token.chain)}\n\n"
        f"{digest}\n\n"
        f"Position size: {analysis.risk.size_sol:.4f} SOL (dry-run)\n"
        f"{token_url(token.chain, token.mint)}"
    )
    snapshot_id = await storage.save_analysis_snapshot(
        token.chain, token.mint, json.dumps(asdict(analysis), ensure_ascii=False)
    )
    keyboard = None
    if config.xai_oauth_client_id and config.xai_oauth_redirect_uri and config.oauth_encryption_key:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Ask Grok", callback_data=f"oauth:ask:{snapshot_id}")
        ]])
    await bot.send_message(
        config.alert_chat_id, text, disable_web_page_preview=True, reply_markup=keyboard
    )
