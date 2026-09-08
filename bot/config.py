from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_ids(raw: str) -> set[int]:
    return {int(x) for x in raw.split(",") if x.strip().isdigit()}


def _parse_chains(raw: str) -> tuple[str, ...]:
    chains = tuple(dict.fromkeys(part.strip().lower() for part in raw.split(",") if part.strip()))
    return chains or ("solana",)


def _parse_urls(raw: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value.strip() for value in raw.split(",") if value.strip()))


@dataclass(frozen=True)
class Config:
    bot_token: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])
    admin_ids: set[int] = field(default_factory=lambda: _parse_ids(os.getenv("ADMIN_IDS", "")))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "pumpguard.db"))
    dashboard_port: int = field(default_factory=lambda: int(os.getenv("DASHBOARD_PORT", "8000")))

    # Grok (xAI) — used for the 4 screening agents. Never used to place trades.
    grok_api_key: str = field(default_factory=lambda: os.getenv("GROK_API_KEY", ""))
    grok_base_url: str = field(
        default_factory=lambda: os.getenv("GROK_BASE_URL", "https://api.x.ai/v1/chat/completions")
    )
    grok_fast_model: str = field(default_factory=lambda: os.getenv("GROK_FAST_MODEL", "grok-4-fast"))
    grok_checker_model: str = field(default_factory=lambda: os.getenv("GROK_CHECKER_MODEL", "grok-4"))
    grok_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("GROK_TIMEOUT_SECONDS", "20")))
    grok_max_retries: int = field(default_factory=lambda: int(os.getenv("GROK_MAX_RETRIES", "3")))
    grok_breaker_failure_threshold: int = field(
        default_factory=lambda: int(os.getenv("GROK_BREAKER_FAILURE_THRESHOLD", "5"))
    )
    grok_breaker_cooldown_seconds: float = field(
        default_factory=lambda: float(os.getenv("GROK_BREAKER_COOLDOWN_SECONDS", "60"))
    )

    # New-launch data feed (PumpPortal's public pump.fun WebSocket feed).
    data_ws_url: str = field(default_factory=lambda: os.getenv("DATA_WS_URL", "wss://pumpportal.fun/api/data"))
    enabled_chains: tuple[str, ...] = field(
        default_factory=lambda: _parse_chains(os.getenv("ENABLED_CHAINS", "solana"))
    )
    base_data_url: str = field(
        default_factory=lambda: os.getenv("BASE_DATA_URL", "https://www.clanker.world/api/tokens")
    )
    base_rpc_url: str = field(default_factory=lambda: os.getenv("BASE_RPC_URL", "https://mainnet.base.org"))
    robinhood_data_url: str = field(
        default_factory=lambda: os.getenv("ROBINHOOD_DATA_URL", "https://hood.fun")
    )
    robinhood_rpc_url: str = field(
        default_factory=lambda: os.getenv("ROBINHOOD_RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
    )
    min_launch_age_seconds: int = field(default_factory=lambda: int(os.getenv("MIN_LAUNCH_AGE_SECONDS", "60")))
    min_unique_buyers: int = field(default_factory=lambda: int(os.getenv("MIN_UNIQUE_BUYERS", "5")))
    copycat_similarity_threshold: float = field(
        default_factory=lambda: float(os.getenv("COPYCAT_SIMILARITY_THRESHOLD", "0.85"))
    )

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
    webhook_urls: tuple[str, ...] = field(default_factory=lambda: _parse_urls(os.getenv("WEBHOOK_URLS", "")))
    public_digest_chat_id: str | None = field(
        default_factory=lambda: os.getenv("PUBLIC_DIGEST_CHAT_ID") or None
    )

    # Optional per-user Grok OAuth. This is separate from the screening API key.
    xai_oauth_client_id: str = field(default_factory=lambda: os.getenv("XAI_OAUTH_CLIENT_ID", ""))
    xai_oauth_client_secret: str = field(default_factory=lambda: os.getenv("XAI_OAUTH_CLIENT_SECRET", ""))
    xai_oauth_redirect_uri: str = field(default_factory=lambda: os.getenv("XAI_OAUTH_REDIRECT_URI", ""))
    oauth_encryption_key: str = field(default_factory=lambda: os.getenv("OAUTH_ENCRYPTION_KEY", ""))


config = Config()
