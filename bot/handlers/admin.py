from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import config
from bot.keyboards import (
    admin_channel_detail_keyboard,
    admin_channels_keyboard,
    admin_root_keyboard,
    back_keyboard,
    cancel_keyboard,
)
from bot.locales.texts import t
from bot.services.storage import Storage
from bot.states import AdminStates

router = Router(name="admin")
logger = logging.getLogger(__name__)

_LANG_FLAG = {"ru": "🇷🇺", "en": "🇬🇧"}


def _is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


async def _user_lang(storage: Storage, user_id: int) -> str:
    user = await storage.get_user(user_id)
    return user.lang if user else "ru"


@router.callback_query(F.data == "admin:open")
async def cb_admin_open(callback: CallbackQuery, storage: Storage, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    lang = await _user_lang(storage, callback.from_user.id)
    await callback.message.edit_text(t(lang, "admin_panel_title"), reply_markup=admin_root_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery, storage: Storage) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    lang = await _user_lang(storage, callback.from_user.id)
    stats = await storage.stats()
    await callback.message.edit_text(t(lang, "stats", **stats), reply_markup=back_keyboard("admin:open"))
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, storage: Storage, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    lang = await _user_lang(storage, callback.from_user.id)
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text(t(lang, "admin_broadcast_prompt"), reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(AdminStates.waiting_broadcast)
async def on_broadcast_content(message: Message, bot: Bot, storage: Storage, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    lang = await _user_lang(storage, message.from_user.id)
    await state.clear()

    user_ids = await storage.all_user_ids()
    await message.answer(t(lang, "broadcast_started", total=len(user_ids)))

    sent = failed = 0
    for user_id in user_ids:
        try:
            await message.copy_to(user_id)
            sent += 1
        except Exception:
            failed += 1
            logger.warning("broadcast failed for %s", user_id, exc_info=True)
        await asyncio.sleep(0.05)

    await message.answer(t(lang, "broadcast_done", sent=sent, failed=failed), reply_markup=back_keyboard("admin:open"))


@router.callback_query(F.data == "admin:channels")
async def cb_admin_channels(callback: CallbackQuery, storage: Storage, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    lang = await _user_lang(storage, callback.from_user.id)
    await callback.message.edit_text(t(lang, "admin_channels_title"), reply_markup=admin_channels_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:channel:") & ~F.data.contains(":set:") & ~F.data.contains(":unset:"))
async def cb_admin_channel_detail(callback: CallbackQuery, storage: Storage) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    target_lang = callback.data.rsplit(":", 1)[1]
    lang = await _user_lang(storage, callback.from_user.id)
    channel = await storage.get_required_channel(target_lang)
    text = t(
        lang, "admin_channel_detail", flag=_LANG_FLAG.get(target_lang, ""), lang=target_lang,
        channel=channel or t(lang, "channels_none"),
    )
    await callback.message.edit_text(text, reply_markup=admin_channel_detail_keyboard(target_lang, bool(channel)))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:channel:set:"))
async def cb_admin_channel_set_start(callback: CallbackQuery, storage: Storage, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    target_lang = callback.data.rsplit(":", 1)[1]
    lang = await _user_lang(storage, callback.from_user.id)
    await state.set_state(AdminStates.waiting_channel)
    await state.update_data(target_lang=target_lang)
    await callback.message.edit_text(
        t(lang, "admin_channel_set_prompt"), reply_markup=cancel_keyboard(f"admin:channel:{target_lang}")
    )
    await callback.answer()


@router.message(AdminStates.waiting_channel)
async def on_channel_username(message: Message, storage: Storage, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    data = await state.get_data()
    target_lang = data.get("target_lang", "ru")
    await state.clear()
    lang = await _user_lang(storage, message.from_user.id)
    channel = (message.text or "").strip()
    if not channel.startswith("@"):
        channel = f"@{channel}"
    await storage.set_required_channel(target_lang, channel)
    await message.answer(
        t(lang, "admin_channel_set_done", lang=target_lang, channel=channel),
        reply_markup=admin_channel_detail_keyboard(target_lang, True),
    )


@router.callback_query(F.data.startswith("admin:channel:unset:"))
async def cb_admin_channel_unset(callback: CallbackQuery, storage: Storage) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    target_lang = callback.data.rsplit(":", 1)[1]
    lang = await _user_lang(storage, callback.from_user.id)
    await storage.set_required_channel(target_lang, None)
    text = t(lang, "admin_channel_unset_done", lang=target_lang)
    await callback.message.edit_text(text, reply_markup=admin_channel_detail_keyboard(target_lang, False))
    await callback.answer()
