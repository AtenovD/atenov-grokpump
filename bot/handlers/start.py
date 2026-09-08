from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import config
from bot.keyboards import back_to_menu_keyboard, language_keyboard, main_menu_keyboard
from bot.locales.texts import t
from bot.services.storage import Storage
from bot.services.chains import chain_label

router = Router(name="start")


def _is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


@router.message(CommandStart())
async def cmd_start(message: Message, storage: Storage) -> None:
    user = await storage.get_user(message.from_user.id)
    if user is None:
        await storage.upsert_user(message.from_user.id, message.from_user.username)
        await message.answer(t("ru", "choose_lang"), reply_markup=language_keyboard())
        return

    await storage.upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(t(user.lang, "welcome"))
    await message.answer(
        t(user.lang, "main_menu_title"), reply_markup=main_menu_keyboard(user.lang, _is_admin(message.from_user.id))
    )


@router.callback_query(F.data.startswith("lang:"))
async def on_lang_chosen(callback: CallbackQuery, storage: Storage) -> None:
    lang = callback.data.split(":", 1)[1]
    await storage.upsert_user(callback.from_user.id, callback.from_user.username, lang=lang)
    await callback.message.edit_text(t(lang, "lang_set"))
    await callback.message.answer(t(lang, "welcome"))
    await callback.message.answer(
        t(lang, "main_menu_title"), reply_markup=main_menu_keyboard(lang, _is_admin(callback.from_user.id))
    )
    await callback.answer()


@router.callback_query(F.data == "menu:root")
async def on_menu_root(callback: CallbackQuery, storage: Storage) -> None:
    user = await storage.get_user(callback.from_user.id)
    lang = user.lang if user else "ru"
    await callback.message.edit_text(
        t(lang, "main_menu_title"), reply_markup=main_menu_keyboard(lang, _is_admin(callback.from_user.id))
    )
    await callback.answer()


@router.callback_query(F.data == "menu:stats")
async def on_stats(callback: CallbackQuery, storage: Storage) -> None:
    user = await storage.get_user(callback.from_user.id)
    lang = user.lang if user else "ru"
    stats = await storage.stats()
    await callback.message.edit_text(t(lang, "stats", **stats), reply_markup=back_to_menu_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "menu:positions")
async def on_positions(callback: CallbackQuery, storage: Storage) -> None:
    user = await storage.get_user(callback.from_user.id)
    lang = user.lang if user else "ru"
    positions = await storage.open_positions()
    if not positions:
        await callback.message.edit_text(t(lang, "positions_empty"), reply_markup=back_to_menu_keyboard(lang))
        await callback.answer()
        return

    lines = [t(lang, "positions_title"), ""]
    for p in positions:
        lines.append(
            t(
                lang, "position_item", chain=chain_label(p.chain),
                symbol=p.symbol or p.mint[:8], entry=p.entry_price,
                size=p.sol_spent, score=p.score,
            )
        )
    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_menu_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "check_sub")
async def on_check_sub(callback: CallbackQuery, storage: Storage) -> None:
    user = await storage.get_user(callback.from_user.id)
    lang = user.lang if user else "ru"
    await callback.answer(t(lang, "subscribe_confirmed"), show_alert=True)
    if callback.message:
        await callback.message.delete()
