from __future__ import annotations

import time

import aiosqlite
from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest

from bot.services.storage import Storage


async def _rows(storage: Storage, sql: str) -> list[tuple]:
    try:
        cursor = await storage.db.execute(sql)
        return await cursor.fetchall()
    except aiosqlite.OperationalError:
        return []


async def render_metrics(storage: Storage, stale_after_seconds: int = 60) -> bytes:
    registry = CollectorRegistry()
    screened = Counter(
        "pumpguard_signals_screened", "Recorded signals reaching each terminal stage", ["stage"],
        registry=registry,
    )
    bought = Counter(
        "pumpguard_signals_bought", "Recorded dry-run buys by terminal stage", ["stage"],
        registry=registry,
    )
    for stage, outcome, count in await _rows(
        storage, "SELECT stage, outcome, COUNT(*) FROM signals GROUP BY stage, outcome"
    ):
        screened.labels(stage=str(stage)).inc(int(count))
        if outcome == "bought":
            bought.labels(stage=str(stage)).inc(int(count))

    positions = Gauge(
        "pumpguard_open_positions", "Current number of open dry-run positions", registry=registry
    )
    position_rows = await _rows(
        storage, "SELECT COUNT(*) FROM positions WHERE status = 'open'"
    )
    positions.set(int(position_rows[0][0]) if position_rows else 0)

    circuit = Gauge(
        "pumpguard_circuit_breaker_state",
        "Current Grok circuit breaker state as a one-hot gauge", ["state"], registry=registry,
    )
    health_rows = await _rows(
        storage, "SELECT component, status, value, updated_at FROM runtime_health"
    )
    health = {str(row[0]): row[1:] for row in health_rows}
    circuit_row = health.get("circuit_breaker", ("unknown", 0, 0))
    circuit_status = str(circuit_row[0])
    if int(time.time()) - int(circuit_row[2]) > stale_after_seconds:
        circuit_status = "unknown"
    for state in ("closed", "open", "half_open", "unknown"):
        circuit.labels(state=state).set(float(state == circuit_status))

    feed = Gauge(
        "pumpguard_price_feed_healthy",
        "Whether the bot reports a fresh healthy price feed", ["chain"], registry=registry,
    )
    feed_updated = Gauge(
        "pumpguard_price_feed_last_report_timestamp_seconds",
        "Unix timestamp of the latest bot price-feed health report", ["chain"], registry=registry,
    )
    now = int(time.time())
    for component, (status, value, updated_at) in health.items():
        if not component.startswith("price_feed:"):
            continue
        chain = component.split(":", 1)[1]
        fresh = now - int(updated_at) <= stale_after_seconds
        feed.labels(chain=chain).set(float(bool(value) and status == "healthy" and fresh))
        feed_updated.labels(chain=chain).set(int(updated_at))

    return generate_latest(registry)
