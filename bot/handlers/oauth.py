from __future__ import annotations

from html import escape

import aiohttp
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import config
from bot.locales.texts import t
from bot.services.oauth import OAuthError, OAuthSettings, XaiOAuthClient, detailed_prompt
from bot.services.storage import Storage

router = Router(name="oauth")


def _settings() -> OAuthSettings:
    return OAuthSettings(
        config.xai_oauth_client_id, config.xai_oauth_client_secret,
        config.xai_oauth_redirect_uri, config.oauth_encryption_key,
    )


async def _lang(storage: Storage, user_id: int) -> str:
    user = await storage.get_user(user_id)
    return user.lang if user else "ru"


@router.callback_query(F.data == "oauth:connect")
async def connect_grok(callback: CallbackQuery, storage: Storage) -> None:
    lang = await _lang(storage, callback.from_user.id)
    try:
        client = XaiOAuthClient(_settings())
        url = await client.begin(storage, callback.from_user.id)
    except OAuthError:
        await callback.answer(t(lang, "oauth_unavailable"), show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔐 x.ai", url=url)
    ]])
    await callback.message.answer(t(lang, "oauth_open_link"), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("oauth:ask:"))
async def ask_grok(callback: CallbackQuery, storage: Storage) -> None:
    lang = await _lang(storage, callback.from_user.id)
    try:
        snapshot_id = int(callback.data.rsplit(":", 1)[1])
        snapshot = await storage.get_analysis_snapshot(snapshot_id)
        if snapshot is None:
            raise OAuthError("signal snapshot not found")
        client = XaiOAuthClient(_settings())
        await callback.answer(t(lang, "oauth_working"))
        async with aiohttp.ClientSession() as session:
            token = await client.access_token(storage, session, callback.from_user.id)
            answer = await client.ask(session, token, detailed_prompt(snapshot))
        safe_answer = escape(answer)
        for offset in range(0, len(safe_answer), 3900):
            await callback.bot.send_message(callback.from_user.id, safe_answer[offset:offset + 3900])
    except OAuthError as exc:
        key = "oauth_needed" if "not connected" in str(exc) else "oauth_failed"
        await callback.bot.send_message(callback.from_user.id, t(lang, key))
