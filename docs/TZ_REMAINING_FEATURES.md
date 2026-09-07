# PumpGuard Bot — Technical Spec: Backtest Engine, Multi-Chain, Web Dashboard

## 0. Context (read this first)

`atenov-pumpguard` is a Telegram bot (Python 3.12, aiogram 3, aiosqlite, aiohttp) that screens new
pump.fun (Solana) token launches through a pipeline of agents and simulates trades. **It never executes
a real trade** — there is exactly one executor (`DryRunExecutor`) and it is intentional that no live
executor exists. Nothing in this spec should introduce real trade execution, real wallets, or private
key handling on any chain.

Current pipeline, in order, for each new token:

1. `bot/services/monitor.py` — WebSocket connection to PumpPortal's public pump.fun feed, yields new `Token` objects.
2. `bot/services/pipeline.py: screen_token()` — orchestrates the rest:
   - code-only filters (age, buyer count)
   - reputation check (`bot/services/reputation.py`) — blocks known-bad creators
   - `Researcher` agent (`bot/services/agents.py: run_researcher`) — free DB lookups, no LLM call
   - `Auditor`, `Narrative`, `Timing` agents — call Grok (xAI) via `bot/services/grok_client.py`, run in parallel
   - `Checker` agent — adversarial final pass on a stronger Grok model, sees all four prior verdicts
   - `RiskManager` (`bot/services/risk.py`) — five arithmetic limits, sizes the position
   - `DryRunExecutor.buy()` (`bot/services/executor.py`) — simulates the entry price and records a `Position` in SQLite
3. `bot/services/price_feed.py: PriceFeed` — separately tracks real bonding-curve prices for open positions via PumpPortal's per-mint trade stream.
4. `bot/services/scheduler.py: run_position_watcher()` — force-closes a position (simulated) the moment its real observed drawdown from entry crosses `STOP_LOSS_PCT`.
5. Every screening outcome (bought, and every skip with its stage/reason) is logged to the `signals` table in SQLite (`bot/services/storage.py`).

Data model you'll be working with (SQLite, `bot/services/storage.py`, table `SCHEMA` string):

- `signals(id, mint, symbol, score, stage, outcome, detail, created_at)` — every screening decision, ever made. `stage` is one of `filter|reputation|scoring|checker|risk|executor`. `outcome` is `skip` or `bought`.
- `positions(mint, symbol, entry_price, sol_spent, score, creator, opened_at, status)` — `status` is `open` or `closed`.
- `creators(creator, rugs, wins, last_seen_at)` — reputation book.
- `seen_tokens(mint, symbol, name, first_seen_at)` — dedup + copycat-name lookups.
- `users`, `required_channels` — Telegram bot user table and the mandatory-subscription-channel gate; not relevant to this spec.

Config lives in `bot/config.py` as a single frozen `Config` dataclass populated from environment
variables (see `.env.example` in the repo root for the full current list). Add new settings the same
way: a field on `Config`, a matching line in `.env.example`, documented in `README.md`'s config table.

Telegram UI conventions used throughout this project (`bot/keyboards.py`, `bot/locales/texts.py`,
`bot/handlers/*.py`): **button-only, no slash commands beyond `/start`**, RU/EN via a `t(lang, key,
**kwargs)` dict-based helper, admin-only actions gated on `user_id in config.admin_ids`. Match this
style for any new bot-side UI; do not add new slash commands.

---

## 1. Backtest Engine

### Goal

Replay the `signals` already logged in SQLite and compute how the pipeline's decisions actually
would have performed, to produce real accuracy numbers instead of anecdotal impressions.

### Scope

This is a **replay/analysis tool over data already collected by the running bot** — it is not a
simulator that invents historical pump.fun data from scratch. It only has something to analyze once
the bot has been running for a while and has accumulated `signals` and `positions` rows.

### Requirements

1. New module `bot/services/backtest.py` exposing at least:
   ```python
   @dataclass
   class BacktestReport:
       total_signals: int
       total_bought: int
       total_skipped: int
       skip_by_stage: dict[str, int]          # e.g. {"scoring": 412, "checker": 88, ...}
       win_rate: float                         # fraction of closed positions with positive PnL
       avg_pnl_pct: float
       median_pnl_pct: float
       best_position: dict | None               # mint/symbol/pnl_pct of the best closed trade
       worst_position: dict | None
       stop_loss_hit_rate: float                # fraction of closed positions that hit the stop-loss
       period_start: int                        # unix timestamp
       period_end: int

   async def run_backtest(storage: Storage, since_days: int | None = None) -> BacktestReport:
       ...
   ```
2. `run_backtest` reads from `signals` and `positions` (join on `mint`) — no network calls, no Grok
   calls, pure SQL + Python aggregation. `since_days=None` means "all recorded history".
3. Add whatever read-only query methods `Storage` needs to support this (e.g. `signals_since(ts)`,
   `closed_positions_since(ts)`) — follow the existing method style in `bot/services/storage.py`
   (plain SQL via `self.db.execute`, no ORM).
4. Telegram exposure: add a **button** "📈 Backtest" to the existing admin panel
   (`bot/keyboards.py: admin_root_keyboard()` and the matching handler in `bot/handlers/admin.py`,
   same pattern as the existing `admin:stats` button). Tapping it runs `run_backtest(storage)` and
   renders the `BacktestReport` as a formatted message (reuse the `t(lang, key, **kwargs)` i18n
   pattern — add new RU/EN keys to `bot/locales/texts.py` for the report layout, do not hardcode
   English or Russian strings directly in the handler).
5. No new external dependencies required for this feature.

### Acceptance criteria

- Unit test (matching the style already used in this repo's manual test scripts — see how
  `run_researcher`/`RiskManager`/`CircuitBreaker` were exercised during development: seed an
  in-memory `Storage(':memory:')` with synthetic `signals`/`positions` rows, call `run_backtest`,
  assert the aggregates come out correct) covering: empty DB (should not crash, all-zero report),
  a mix of wins/losses, and `since_days` filtering actually excluding older rows.
- The admin "📈 Backtest" button renders without crashing on a fresh DB with zero signals.

---

## 2. Multi-Chain Support (Base + Robinhood Chain, alongside existing Solana/pump.fun)

### Goal

Run the same screening pipeline (Researcher → Auditor → Narrative → Timing → Checker → Risk →
Dry-run buy → real-price stop-loss watcher) against new-token launches on two additional chains:

- **Base**, via the **Clanker** launchpad
- **Robinhood Chain**, via the **hood.fun** launchpad (Pons is the other major launchpad there; prefer
  hood.fun as the closer match to pump.fun's bonding-curve mechanics, per public research — verify
  this is still accurate when you start, these platforms move fast)

### Important: research before coding

Do not guess API shapes. Before writing the connector for each chain:

1. Find each launchpad's actual public data source for new launches — a WebSocket feed, a subgraph,
   an indexer REST API, or (last resort) direct RPC log subscription against the launchpad's
   on-chain program/contract. Solana's PumpPortal (already integrated, see `bot/services/monitor.py`)
   is the existing example of "a friendly third-party indexer already did this work" — check first
   whether Clanker and hood.fun have an equivalent before building a raw RPC log-scraper.
2. Confirm the bonding-curve math for each platform (constant-product, linear, or something else) —
   it will not necessarily match pump.fun's formula (`price = virtual_sol_reserves /
   virtual_token_reserves`, see `bot/services/price_feed.py: PriceFeed._price_from_trade`). Get this
   wrong and every real-price/stop-loss number for that chain is silently fake — this is the exact
   bug class that was just fixed for Solana in this repo (see git history: the previous version used
   `random.uniform()` for exit prices, which made all reported PnL meaningless).
3. Both chains are EVM-compatible (Base is an Ethereum L2; Robinhood Chain, per public documentation
   at the time this spec was written, is Arbitrum-based) — you likely need `web3.py` and an RPC
   endpoint (a public one, or ask for a provider API key as a new config value) for at least
   fallback/verification, even if a friendly indexer exists for day-to-day monitoring.

### Architecture requirement: chain must be a first-class dimension, not a bolt-on

This is the largest single design decision in this spec. Do it properly:

1. Add a `chain: str` field to the `Token`, `Position`, and `signals`/`seen_tokens`/`positions`/
   `creators` rows (`chain` values: `"solana"`, `"base"`, `"robinhood"`). A creator address on Base
   and a creator address on Solana are unrelated identities — the reputation book, dedup, and
   copycat-name detection must all be scoped per-chain (e.g. `WHERE chain = ? AND creator = ?`), not
   global. Write a SQLite migration path (`ALTER TABLE ... ADD COLUMN chain TEXT NOT NULL DEFAULT
   'solana'` for existing tables) so upgrading an already-running bot doesn't lose history.
2. Restructure `bot/services/monitor.py` and `bot/services/price_feed.py` into a small per-chain
   plugin structure, e.g.:
   ```
   bot/services/chains/
     __init__.py        # ChainAdapter protocol/ABC: stream_new_tokens(), get_price(mint), chain_id
     solana.py          # today's PumpPortal logic, moved here, implementing ChainAdapter
     base.py            # Clanker
     robinhood.py       # hood.fun
   ```
   `bot/services/scheduler.py: run_monitor_loop` should run one instance of the loop **per configured
   chain adapter**, all writing into the same `Storage`/pipeline, tagging every `Token` with its
   `chain`. Do not duplicate `screen_token`'s logic per chain — the pipeline stages (agents, risk,
   reputation) stay chain-agnostic; only monitor/price-feed/executor are chain-specific.
3. `DryRunExecutor` stays chain-agnostic (it already takes a price and returns a simulated fill — no
   change needed there beyond accepting whatever price each chain's `PriceFeed` produces).
4. Config: add `ENABLED_CHAINS` (comma-separated, e.g. `solana,base`) so an operator can run a subset.
   Each chain gets its own data-source URL / RPC endpoint config vars following the existing
   `DATA_WS_URL` naming pattern (e.g. `BASE_DATA_URL`, `ROBINHOOD_DATA_URL`, plus an RPC URL each if
   needed for price verification).
5. Telegram-facing changes: the alert message built in `bot/services/pipeline.py: broadcast_signal`
   and the "📂 Open positions" screen (`bot/handlers/start.py: on_positions`) must show which chain a
   token is on. Add a small chain-name/emoji mapping (e.g. 🟣 Solana, 🔵 Base, 🟢 Robinhood) — keep it
   in one place (e.g. a `CHAIN_LABELS` dict near the top of `bot/keyboards.py` or a new small
   `bot/services/chains/__init__.py` constant) so it's not duplicated across handlers.

### Explicit non-goals (do not build these)

- No live execution on any chain. `DryRunExecutor` remains the only executor everywhere.
- No wallet creation, no private key storage, no signing, on any chain.

### Acceptance criteria

- With `ENABLED_CHAINS=solana` (i.e. today's behavior), the bot must behave identically to before this
  work — this is a refactor-then-extend, not a rewrite of working Solana behavior. Run the existing
  manual test scripts used during this repo's development (mocked-agent `screen_token` pass/reject
  cases, the stop-loss watcher test, the circuit breaker test) against the refactored code and confirm
  they still pass unmodified or with only import-path changes.
- With `ENABLED_CHAINS=solana,base,robinhood`, new tokens from all three sources appear (tagged with
  the correct `chain`) in `/stats` and the admin panel, and reputation/dedup/copycat-detection are
  verifiably scoped per-chain (write a test: the same creator address string rugging on `solana` must
  not block that same string from launching cleanly on `base`).
- Document in `README.md` exactly what real, working data source and RPC/indexer you ended up using
  for Base and Robinhood Chain, since this spec deliberately doesn't prescribe one and it may have
  changed by the time you implement this — this is a young, fast-moving part of both ecosystems.

---

## 3. Read-only Web Dashboard

### Goal

A simple, read-only web page showing the screening funnel and current state — a companion to the
Telegram bot, not a replacement for it. No login-gated multi-user features, no write actions from the
web UI (no buying/selling/config-changing from the dashboard — that stays in Telegram's admin panel).

### Requirements

1. New standalone service, `dashboard/` at the repo root (sibling to `bot/`), FastAPI + a single
   Jinja2 template or a tiny bit of vanilla JS hitting a JSON API — keep the stack minimal, this does
   not need a frontend build pipeline (no React/webpack). Reuse `bot/services/storage.py`'s `Storage`
   class directly (same SQLite file, read-only access pattern — open a second connection, don't share
   the bot process's connection object across processes).
2. Pages/endpoints:
   - `GET /` — funnel view: for a selectable time window (last 1h/24h/7d), a bar/number breakdown of
     `signals` by `stage`/`outcome` (how many filtered at each stage, how many bought), plus the
     `BacktestReport` summary numbers from section 1 of this spec.
   - `GET /positions` — table of currently open positions (mint, chain, symbol, entry price, current
     price from the same `PriceFeed` data the bot uses — read the latest known price out of SQLite if
     you log price snapshots, or note in the dashboard if "live price" isn't available without a
     shared process; do not spin up a second competing WebSocket connection to the same feed purely
     for the dashboard if it can be avoided — prefer having the bot process periodically snapshot
     `PriceFeed` state to SQLite for the dashboard to read).
   - `GET /api/stats` — JSON version of the same numbers `storage.stats()` already returns (see
     `bot/handlers/start.py: on_stats` for the existing shape), for the frontend JS to poll.
3. Auth: this is meant to run behind the operator's own reverse proxy / VPN / basic-auth at the
   nginx/Caddy layer — do not build a username/password system into the FastAPI app itself. Document
   this assumption clearly in `README.md` ("do not expose this port publicly without your own auth in
   front of it").
4. Deployment: add a `dashboard` service to `docker-compose.yml` (new container, same image or a
   lightweight one, mounting/sharing the SQLite file with the bot container via a volume), and a
   `deploy/pumpguard-dashboard.service` systemd unit mirroring the existing `deploy/pumpguard-bot.service`
   for non-Docker deployments. Pick a default port that doesn't collide with anything else in this
   repo (nothing currently listens on a port — this is the first service in the repo that needs one;
   `8000` is a reasonable default, make it configurable via a `DASHBOARD_PORT` env var).
5. New dependencies needed: `fastapi`, `uvicorn`, `jinja2` — add them to a separate
   `requirements-dashboard.txt` (do not bloat the bot's own `requirements.txt` with a web framework it
   doesn't need), matching the pattern already used in this project's sibling repo `atenov-uniqvid`
   for its optional `requirements-pot.txt`.

### Acceptance criteria

- `uvicorn dashboard.main:app` starts cleanly against an empty (freshly created) SQLite DB and renders
  all pages without crashing (zero signals, zero positions is a valid, common state — must render
  "nothing yet" rather than error).
- The dashboard process never writes to the SQLite database — verify by code review that only
  `SELECT` queries are issued from `dashboard/`.
- Manually verified in a browser: funnel numbers on `/` match what `/stats` reports in Telegram for
  the same bot instance/database.

---

## Delivery format

Please open one pull request per section (1, 2, 3 above) against `main`, each with its own commit(s),
rather than one combined PR — they're independent enough to review and merge separately, and section 2
(multi-chain) is materially riskier/larger than the other two and shouldn't block on it.
