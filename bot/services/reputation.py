from __future__ import annotations

from bot.config import config
from bot.services.storage import Storage


class ReputationBook:
    """Tracks how a token creator's past launches turned out, blocks repeat ruggers."""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    async def is_blocked(self, creator: str | None, chain: str = "robinhood") -> str | None:
        if not creator:
            return None
        rugs = await self.storage.creator_rugs(creator, chain)
        if rugs >= config.block_creator_after_rugs:
            return f"creator has {rugs} prior rug(s)"
        return None

    async def record_outcome(
        self, creator: str | None, pnl_pct: float, chain: str = "robinhood"
    ) -> None:
        if not creator:
            return
        is_rug = -pnl_pct >= config.rug_loss_pct
        await self.storage.record_creator_outcome(creator, is_rug, chain)

    async def cleanup(self) -> int:
        return await self.storage.forget_stale_creators(config.forget_creators_after_days)
