from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_ids(raw: str) -> set[int]:
    return {int(x) for x in raw.split(",") if x.strip().isdigit()}


@dataclass(frozen=True)
class Config:
    bot_token: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])
    admin_ids: set[int] = field(default_factory=lambda: _parse_ids(os.getenv("ADMIN_IDS", "")))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "pumpguard.db"))

    # Grok (xAI) — used for the 4 screening agents. Never used to place trades.
    grok_api_key: str = field(default_factory=lambda: os.getenv("GROK_API_KEY", ""))
    grok_base_url: str = field(
        default_factory=lambda: os.getenv("GROK_BASE_URL", "https://api.x.ai/v1/chat/completions")
    )
    grok_fast_model: str = field(default_factory=lambda: os.getenv("GROK_FAST_MODEL", "grok-4-fast"))
    grok_checker_model: str = field(default_factory=lambda: os.getenv("GROK_CHECKER_MODEL", "grok-4"))
    grok_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("GROK_TIMEOUT_SECONDS", "20")))
    grok_max_retries: int = field(default_factory=lambda: int(os.getenv("GROK_MAX_RETRIES", "3")))

    # New-launch data feed (PumpPortal's public pump.fun WebSocket feed).
    data_ws_url: str = field(default_factory=lambda: os.getenv("DATA_WS_URL", "wss://pumpportal.fun/api/data"))
    min_launch_age_seconds: int = field(default_factory=lambda: int(os.getenv("MIN_LAUNCH_AGE_SECONDS", "60")))
    min_unique_buyers: int = field(default_factory=lambda: int(os.getenv("MIN_UNIQUE_BUYERS", "5")))

    # Risk manager — five independent limits, checked before any signal is surfaced.
    max_sol_per_trade: float = field(default_factory=lambda: float(os.getenv("MAX_SOL_PER_TRADE", "0.5")))
    daily_loss_limit_sol: float = field(default_factory=lambda: float(os.getenv("DAILY_LOSS_LIMIT_SOL", "2.0")))
    max_trades_per_day: int = field(default_factory=lambda: int(os.getenv("MAX_TRADES_PER_DAY", "10")))
    max_open_positions: int = field(default_factory=lambda: int(os.getenv("MAX_OPEN_POSITIONS", "5")))
    stop_loss_pct: float = field(default_factory=lambda: float(os.getenv("STOP_LOSS_PCT", "35")))

    # Reputation book — creators are blocked after this many rugs.
    rug_loss_pct: float = field(default_factory=lambda: float(os.getenv("RUG_LOSS_PCT", "60")))
    block_creator_after_rugs: int = field(default_factory=lambda: int(os.getenv("BLOCK_CREATOR_AFTER_RUGS", "1")))
    forget_creators_after_days: int = field(default_factory=lambda: int(os.getenv("FORGET_CREATORS_AFTER_DAYS", "90")))

    alert_chat_id: str | None = field(default_factory=lambda: os.getenv("ALERT_CHAT_ID") or None)


config = Config()
