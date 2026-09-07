from __future__ import annotations

TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        "choose_lang": "Привет! Выбери язык:",
        "lang_set": "Язык установлен: Русский 🇷🇺",
        "welcome": (
            "Я слежу за новыми токенами на pump.fun и прогоняю каждый через 4 AI-агента на Grok "
            "(аудитор, нарратив, тайминг, финальный проверяющий) плюс risk-менеджер и книгу репутации "
            "криэйторов.\n\n⚠️ Это исследовательский инструмент. Все сделки — <b>dry-run</b> (симуляция), "
            "реальные деньги никогда не используются."
        ),
        "main_menu_title": "Выбери действие:",
        "btn_stats": "📊 Статистика",
        "btn_positions": "📂 Открытые позиции",
        "btn_back_menu": "⬅ В меню",
        "positions_title": "📂 Открытые позиции (dry-run):",
        "positions_empty": "Сейчас нет открытых позиций.",
        "position_item": "• {symbol} — вход {entry:.6f}, размер {size:.4f} SOL, score {score:.2f}",
        "stats": (
            "📊 Статистика\n\n"
            "Пользователей: {users_total}\n"
            "Проверено токенов за 24ч: {screened_24h}\n"
            "Куплено (dry-run) за 24ч: {bought_24h}\n"
            "Сделок сегодня: {trades_today}\n"
            "PnL за сегодня: {pnl_today:+.4f} SOL\n"
            "Открытых позиций: {open_positions}\n"
            "Заблокированных криэйторов: {blocked_creators}"
        ),
        "admin_panel_title": "🛠 Админ-панель",
        "admin_broadcast_prompt": "Пришли сообщение для рассылки всем пользователям.",
        "broadcast_started": "📣 Рассылка начата ({total} получателей)...",
        "broadcast_done": "📣 Рассылка завершена: доставлено {sent}, ошибок {failed}.",
        "admin_channels_title": "📢 Обязательные каналы подписки",
        "admin_channel_detail": "{flag} Язык: {lang}\nТекущий канал: {channel}",
        "admin_channel_set_prompt": "Пришли username канала (например, @my_channel). Бот должен быть админом в этом канале.",
        "admin_channel_set_done": "✅ Канал для {lang} установлен: {channel}",
        "admin_channel_unset_done": "✅ Обязательная подписка для {lang} отключена.",
        "channels_none": "не задан",
        "subscribe_required": "🔒 Чтобы пользоваться ботом, подпишись на канал {channel}, затем нажми «Я подписался».",
        "subscribe_button": "📢 Открыть канал",
        "subscribe_check_button": "✅ Я подписался",
        "subscribe_still_not": "❌ Пока не вижу подписку. Подпишись и попробуй снова.",
        "subscribe_confirmed": "✅ Подписка подтверждена, теперь бот доступен!",
        "risk_disclaimer": (
            "⚠️ Мемкоины на бондинговой кривой обычно теряют стоимость полностью. Этот бот не размещает "
            "реальные сделки и не является финансовым советом."
        ),
    },
    "en": {
        "choose_lang": "Hi! Choose your language:",
        "lang_set": "Language set: English 🇬🇧",
        "welcome": (
            "I watch new pump.fun token launches and screen each one through 4 Grok-powered agents "
            "(auditor, narrative, timing, final adversarial checker), plus a risk manager and a creator "
            "reputation book.\n\n⚠️ This is a research tool. All trades are <b>dry-run</b> (simulated) — "
            "real money is never used."
        ),
        "main_menu_title": "Choose an action:",
        "btn_stats": "📊 Stats",
        "btn_positions": "📂 Open positions",
        "btn_back_menu": "⬅ Menu",
        "positions_title": "📂 Open positions (dry-run):",
        "positions_empty": "No open positions right now.",
        "position_item": "• {symbol} — entry {entry:.6f}, size {size:.4f} SOL, score {score:.2f}",
        "stats": (
            "📊 Stats\n\n"
            "Users: {users_total}\n"
            "Tokens screened (24h): {screened_24h}\n"
            "Bought (dry-run, 24h): {bought_24h}\n"
            "Trades today: {trades_today}\n"
            "PnL today: {pnl_today:+.4f} SOL\n"
            "Open positions: {open_positions}\n"
            "Blocked creators: {blocked_creators}"
        ),
        "admin_panel_title": "🛠 Admin panel",
        "admin_broadcast_prompt": "Send the message you want to broadcast to all users.",
        "broadcast_started": "📣 Broadcast started ({total} recipients)...",
        "broadcast_done": "📣 Broadcast finished: delivered {sent}, failed {failed}.",
        "admin_channels_title": "📢 Mandatory subscription channels",
        "admin_channel_detail": "{flag} Language: {lang}\nCurrent channel: {channel}",
        "admin_channel_set_prompt": "Send the channel username (e.g. @my_channel). The bot must be an admin in that channel.",
        "admin_channel_set_done": "✅ Channel for {lang} set to: {channel}",
        "admin_channel_unset_done": "✅ Mandatory subscription for {lang} disabled.",
        "channels_none": "not set",
        "subscribe_required": "🔒 To use this bot, subscribe to {channel}, then tap \"I've subscribed\".",
        "subscribe_button": "📢 Open channel",
        "subscribe_check_button": "✅ I've subscribed",
        "subscribe_still_not": "❌ Still not seeing your subscription. Subscribe and try again.",
        "subscribe_confirmed": "✅ Subscription confirmed, the bot is now available!",
        "risk_disclaimer": (
            "⚠️ Bonding-curve memecoins usually lose their value entirely. This bot never places real "
            "trades and is not financial advice."
        ),
    },
}


def t(lang: str, key: str, **kwargs: object) -> str:
    lang = lang if lang in TEXTS else "ru"
    template = TEXTS[lang].get(key, key)
    return template.format(**kwargs) if kwargs else template
