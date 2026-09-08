from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

from bot.services.storage import Storage


@dataclass
class BacktestReport:
    total_signals: int
    total_bought: int
    total_skipped: int
    skip_by_stage: dict[str, int]
    win_rate: float
    avg_pnl_pct: float
    median_pnl_pct: float
    best_position: dict | None
    worst_position: dict | None
    stop_loss_hit_rate: float
    period_start: int
    period_end: int


async def run_backtest(storage: Storage, since_days: int | None = None) -> BacktestReport:
    """Aggregate recorded screening outcomes and closed dry-run positions.

    Positions closed by releases predating exit-price persistence still count as
    closed, but cannot contribute to PnL-derived metrics.
    """
    period_end = int(time.time())
    cutoff = None if since_days is None else period_end - max(since_days, 0) * 86400
    signals = await storage.signals_since(cutoff)
    positions = await storage.closed_positions_since(cutoff)

    skipped = [signal for signal in signals if signal["outcome"] == "skip"]
    bought = [signal for signal in signals if signal["outcome"] == "bought"]
    skip_by_stage: dict[str, int] = {}
    for signal in skipped:
        stage = str(signal["stage"])
        skip_by_stage[stage] = skip_by_stage.get(stage, 0) + 1

    measured: list[dict[str, object]] = []
    for position in positions:
        if position.exit_price is None or position.entry_price <= 0:
            continue
        pnl_pct = (position.exit_price - position.entry_price) / position.entry_price * 100
        measured.append({"mint": position.mint, "symbol": position.symbol, "pnl_pct": pnl_pct})

    pnl_values = [float(position["pnl_pct"]) for position in measured]
    best = max(measured, key=lambda item: float(item["pnl_pct"]), default=None)
    worst = min(measured, key=lambda item: float(item["pnl_pct"]), default=None)
    stop_loss_hits = sum(position.close_reason == "stop_loss" for position in positions)

    timestamps = [int(signal["created_at"]) for signal in signals]
    timestamps.extend(
        position.closed_at or position.opened_at for position in positions
    )
    period_start = min(timestamps) if timestamps else (cutoff if cutoff is not None else period_end)

    return BacktestReport(
        total_signals=len(signals),
        total_bought=len(bought),
        total_skipped=len(skipped),
        skip_by_stage=skip_by_stage,
        win_rate=(sum(value > 0 for value in pnl_values) / len(pnl_values)) if pnl_values else 0.0,
        avg_pnl_pct=statistics.fmean(pnl_values) if pnl_values else 0.0,
        median_pnl_pct=statistics.median(pnl_values) if pnl_values else 0.0,
        best_position=best,
        worst_position=worst,
        stop_loss_hit_rate=(stop_loss_hits / len(positions)) if positions else 0.0,
        period_start=period_start,
        period_end=period_end,
    )
