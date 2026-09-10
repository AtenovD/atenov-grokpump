from __future__ import annotations

from bot.config import config
from bot.locales.texts import t

GROK_CONSOLE_URL = "https://console.x.ai/team/default/api-keys"
GET_CHAT_ID_BOT = "@RawDataBot"


def setup_checklist(lang: str) -> str | None:
    """Renders the operator setup checklist for whatever is still missing.

    Returns None once GROK_API_KEY and ALERT_CHAT_ID are both set - this is
    the entire signal a returning admin gets that there's nothing left to do,
    no separate "first run" flag to track in storage.
    """
    items: list[str] = []
    if not config.grok_api_key:
        items.append(t(lang, "setup_item_grok", link=GROK_CONSOLE_URL))
    if not config.alert_chat_id:
        items.append(t(lang, "setup_item_alert_chat", id_bot=GET_CHAT_ID_BOT))

    if not items:
        return None

    parts = [t(lang, "setup_checklist_title"), ""]
    for item in items:
        parts.append(item)
        parts.append("")
    parts.append(t(lang, "setup_checklist_footer"))
    return "\n".join(parts)
