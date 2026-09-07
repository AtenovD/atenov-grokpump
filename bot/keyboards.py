from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locales.texts import t


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )


def main_menu_keyboard(lang: str, is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, "btn_stats"), callback_data="menu:stats")],
        [InlineKeyboardButton(text=t(lang, "btn_positions"), callback_data="menu:positions")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 Admin panel", callback_data="admin:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_back_menu"), callback_data="menu:root")]]
    )


def admin_root_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Stats", callback_data="admin:stats")],
            [InlineKeyboardButton(text="📣 Broadcast", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="📢 Channels", callback_data="admin:channels")],
            [InlineKeyboardButton(text="⬅ Back", callback_data="menu:root")],
        ]
    )


def back_keyboard(target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅ Back", callback_data=target)]])


def cancel_keyboard(target: str = "admin:open") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✖ Cancel", callback_data=target)]])


def admin_channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 RU channel", callback_data="admin:channel:ru"),
                InlineKeyboardButton(text="🇬🇧 EN channel", callback_data="admin:channel:en"),
            ],
            [InlineKeyboardButton(text="⬅ Back", callback_data="admin:open")],
        ]
    )


def admin_channel_detail_keyboard(lang: str, has_channel: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="✏️ Set channel", callback_data=f"admin:channel:set:{lang}")]]
    if has_channel:
        rows.append([InlineKeyboardButton(text="🗑 Unset channel", callback_data=f"admin:channel:unset:{lang}")])
    rows.append([InlineKeyboardButton(text="⬅ Back", callback_data="admin:channels")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
