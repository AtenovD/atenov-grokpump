from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject

from bot.config import config
from bot.locales.texts import t
from bot.services.storage import Storage

logger = logging.getLogger(__name__)

_OK_STATUSES = {"member", "administrator", "creator"}
_RECHECK_CALLBACK = "check_sub"
_EXEMPT_COMMANDS = ("/start",)


def _channel_display(channel: str) -> str:
    return channel if channel.startswith("@") else f"@{channel}"


def _channel_url(channel: str) -> str:
    return f"https://t.me/{_channel_display(channel).lstrip('@')}"


def _subscribe_keyboard(lang: str, channel: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "subscribe_button"), url=_channel_url(channel))],
            [InlineKeyboardButton(text=t(lang, "subscribe_check_button"), callback_data=_RECHECK_CALLBACK)],
        ]
    )


async def _is_subscribed(bot: Any, channel: str, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=_channel_display(channel), user_id=user_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        logger.warning("could not check subscription for channel %s", channel)
        return True  # fail-open: a misconfigured channel must not lock out every user
    if member.status in _OK_STATUSES:
        return True
    if member.status == "restricted":
        return bool(getattr(member, "is_member", False))
    return False


class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None or user.id in config.admin_ids:
            return await handler(event, data)

        if isinstance(event, Message) and event.text and event.text.startswith(_EXEMPT_COMMANDS):
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data and event.data.startswith("lang:"):
            return await handler(event, data)

        user_record = await self._storage.get_user(user.id)
        lang = user_record.lang if user_record else "ru"

        channel = await self._storage.get_required_channel(lang)
        if not channel:
            return await handler(event, data)

        if await _is_subscribed(event.bot, channel, user.id):
            return await handler(event, data)

        if isinstance(event, CallbackQuery) and event.data == _RECHECK_CALLBACK:
            await event.answer(t(lang, "subscribe_still_not"), show_alert=True)
            return None

        prompt = t(lang, "subscribe_required", channel=_channel_display(channel))
        keyboard = _subscribe_keyboard(lang, channel)
        if isinstance(event, CallbackQuery):
            await event.answer()
            if event.message:
                await event.message.answer(prompt, reply_markup=keyboard)
        elif isinstance(event, Message):
            await event.answer(prompt, reply_markup=keyboard)
        return None
