<p align="center">
  <img src="assets/hero-banner.png" alt="grokbot-pumpfun" width="100%">
</p>

<p align="center">
  <a href="https://github.com/AtenovD/grokbot-pumpfun/actions/workflows/ci.yml"><img src="https://github.com/AtenovD/grokbot-pumpfun/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="https://railway.com/new/template?template=https%3A%2F%2Fgithub.com%2FAtenovD%2Fgrokbot-pumpfun&amp;envs=BOT_TOKEN%2CADMIN_IDS%2CGROK_API_KEY"><img src="https://railway.com/button.svg" alt="Deploy on Railway"></a>
  <a href="https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FAtenovD%2Fgrokbot-pumpfun"><img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render"></a>
</p>

<p align="center">
  <a href="https://github.com/AtenovD/grokbot-pumpfun/stargazers"><img src="https://img.shields.io/github/stars/AtenovD/grokbot-pumpfun?style=for-the-badge&color=yellow" alt="Stars"></a>
  <a href="https://github.com/AtenovD/grokbot-pumpfun/blob/main/LICENSE"><img src="https://img.shields.io/github/license/AtenovD/grokbot-pumpfun?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/AtenovD/grokbot-pumpfun/commits/main"><img src="https://img.shields.io/github/last-commit/AtenovD/grokbot-pumpfun?style=for-the-badge" alt="Last commit"></a>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Powered%20by-Grok-FF6B00?style=for-the-badge" alt="Powered by Grok">
  <img src="https://img.shields.io/badge/chain-Robinhood%20Chain-00C805?style=for-the-badge" alt="Robinhood Chain">
  <img src="https://img.shields.io/badge/execution-dry--run%20only-brightgreen?style=for-the-badge" alt="Dry-run only">
  <img src="https://img.shields.io/badge/NFT-screener-EC4899?style=for-the-badge" alt="NFT screener">
</p>

<p align="center">
  A Telegram bot that screens new Robinhood Chain / hood.fun token launches through four Grok-powered agents, a risk manager, and a creator reputation book - then simulates the trade. No live execution, ever.
</p>

<table align="center">
  <tr>
    <td align="center"><img src="https://img.shields.io/badge/deploy-000000?style=for-the-badge&logo=railway&logoColor=white" alt="deploy"></td>
    <td align="center"><a href="https://railway.com/new/template?template=https%3A%2F%2Fgithub.com%2FAtenovD%2Fgrokbot-pumpfun&envs=BOT_TOKEN%2CADMIN_IDS%2CGROK_API_KEY"><img src="https://img.shields.io/badge/RAILWAY-one--click-0B0D0E?style=for-the-badge&logo=railway&logoColor=%23B14EFF" alt="Railway one-click deploy"></a></td>
    <td align="center"><img src="https://img.shields.io/badge/deploy-000000?style=for-the-badge&logo=render&logoColor=white" alt="deploy"></td>
    <td align="center"><a href="https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FAtenovD%2Fgrokbot-pumpfun"><img src="https://img.shields.io/badge/RENDER-blueprint-00C7B7?style=for-the-badge&logo=render&logoColor=white" alt="Render blueprint deploy"></a></td>
  </tr>
  <tr>
    <td align="center"><img src="https://img.shields.io/badge/self--host-000000?style=for-the-badge&logo=docker&logoColor=white" alt="self-host"></td>
    <td align="center"><a href="#deploy-with-docker"><img src="https://img.shields.io/badge/DOCKER-compose%20up-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose"></a></td>
    <td align="center"><img src="https://img.shields.io/badge/self--host-000000?style=for-the-badge&logo=linux&logoColor=white" alt="self-host"></td>
    <td align="center"><a href="#deploy-on-a-vps-systemd"><img src="https://img.shields.io/badge/VPS-systemd-F7A41D?style=for-the-badge&logo=linux&logoColor=white" alt="VPS systemd deploy"></a></td>
  </tr>
  <tr>
    <td align="center"><img src="https://img.shields.io/badge/install-000000?style=for-the-badge&logo=python&logoColor=white" alt="install"></td>
    <td align="center"><a href="#quick-start"><img src="https://img.shields.io/badge/PIP-requirements.txt-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="pip install"></a></td>
    <td align="center"><img src="https://img.shields.io/badge/dashboard-000000?style=for-the-badge&logo=fastapi&logoColor=white" alt="dashboard"></td>
    <td align="center"><a href="#read-only-dashboard"><img src="https://img.shields.io/badge/READ--ONLY-live%20stats-009688?style=for-the-badge" alt="read-only dashboard"></a></td>
  </tr>
  <tr>
    <td align="center"><img src="https://img.shields.io/badge/webhooks-000000?style=for-the-badge&logo=zapier&logoColor=white" alt="webhooks"></td>
    <td align="center"><a href="docs/webhook-schema.md"><img src="https://img.shields.io/badge/WEBHOOKS-v1%20schema-D9364A?style=for-the-badge" alt="webhook schema docs"></a></td>
    <td align="center"><img src="https://img.shields.io/badge/add%20a%20chain-000000?style=for-the-badge" alt="add a chain"></td>
    <td align="center"><a href="docs/adding-a-chain.md"><img src="https://img.shields.io/badge/CONTRIBUTOR%20DOCS-adapters-6B7280?style=for-the-badge" alt="adding a chain adapter"></a></td>
  </tr>
  <tr>
    <td align="center"><img src="https://img.shields.io/badge/new-000000?style=for-the-badge" alt="new"></td>
    <td align="center"><a href="#nft-screener-robinhood-chain"><img src="https://img.shields.io/badge/NFT%20SCREENER-floor--sweep%20%2B%20cross--signal-EC4899?style=for-the-badge" alt="NFT screener"></a></td>
  </tr>
</table>

<p align="center">
  <img src="assets/chat-preview.svg" alt="PumpGuard Bot chat preview" width="100%">
</p>

## ⚠️ What this is and isn't

This is a **research/screening tool**, not a trading bot. Every "buy" and "sell" is simulated (dry-run): no wallet, no signing, no on-chain transaction. Bonding-curve memecoins on pump.fun routinely lose their entire value. Nothing here is financial advice, and there is no live executor to wire up - that's a deliberately different, much higher-stakes piece of software that this project does not include.

<p align="center">
  <img src="assets/dry-run-only.png" alt="Dry-run only - no wallets, no signing, no live execution" width="60%">
</p>

## Features

<p align="center">
  <img src="assets/pipeline-diagram.png" alt="Screening pipeline: filter, analyze, evaluate, execute" width="100%">
</p>

- **Robinhood Chain launch monitor** - watches hood.fun launches on Robinhood Chain, filters by age and buyer count before spending a single Grok call
- **Five agents**, cheapest first:
  - **Researcher** - free DB lookups before any Grok call: has this creator rugged before, and does this name/symbol exactly or semantically copy a recent token
  - **Auditor** (Grok) - looks for wash trading / bundled buys in the trade and holder data
  - **Narrative** (Grok) - scores the meme's attention potential from its name/symbol
  - **Timing** (Grok) - judges the current window using only this bot's own observed launch/outcome rate (no external price feeds)
  - **Checker** (Grok, stronger model) - an adversarial final pass given all four prior verdicts, explicitly looking for a reason to reject
- **Real price tracking** - open dry-run positions are watched against the chain's actual bonding-curve or DEX-pool price, not a random number
- **Real stop-loss** - a position is force-closed the moment its real observed drawdown from entry crosses `STOP_LOSS_PCT`
- **Circuit breaker on Grok** - after several consecutive failures, the pipeline stops calling Grok for a cooldown window instead of hammering a struggling API on every new launch
- **Explainability digest** - the four agent verdicts are synthesized by Grok into one short, readable paragraph for the alert, instead of four raw JSON summaries
- **Optional user Grok OAuth** - users can connect their own Grok account with authorization-code PKCE and request a fresh, detailed second opinion for a signal. Encrypted user tokens never replace the bot's core `GROK_API_KEY` pipeline
- **Prompt-injection resistant** - token symbol/name/description are attacker-controlled. They're sanitized and every agent prompt explicitly frames them as data, not instructions, before anything reaches Grok
- **Risk manager** - five independent limits: max SOL per trade, daily loss limit, max trades/day, max open positions, stop-loss - pure arithmetic, no model involved, and the last gate before a (simulated) trade
- **Reputation book** - creators are blocked after their tracked launches rug, forgotten after a configurable number of days
- **Dry-run executor** - simulates entry/exit at real observed prices, feeding the reputation book and daily counters exactly like a live executor would
- **Backtest report** - replays recorded signals and closed dry-run positions to show funnel counts, win rate, PnL distribution, and stop-loss frequency
- **Weekly public digest** - optionally publishes the previous seven days of recorded backtest performance to a separate public channel
- **Button-only Telegram frontend**: RU/EN language picker, stats, open positions, optional mandatory-subscription gate, button-driven admin panel - no slash commands beyond `/start`
- **Read-only web dashboard** - responsive funnel, recorded-performance summary, open positions, and a polling JSON stats endpoint without a second market-data connection
- **Versioned signal webhooks** - optionally POST every passing `TokenAnalysis` to multiple integrations with one retry and a stable v1 JSON envelope
- **Prometheus metrics** - dashboard `/metrics` exposes cumulative screening outcomes, positions, Grok circuit-breaker state, and per-chain price-feed health
- **NFT screener** (optional) - a second, independent pipeline screens new Robinhood Chain NFT collections for wash-minting and hype, alert-only
- **Floor-sweep alerts** - watches every screened collection's floor price and alerts on a sudden collapse (possible rug) or spike (possible breakout)
- **Cross-surface signal** - flags when the same creator address launches both a token and an NFT collection on Robinhood Chain

## Stack

Python 3.12, [aiogram 3](https://docs.aiogram.dev/), aiohttp, `websockets`, aiosqlite. Optional FastAPI/Jinja dashboard. Grok API (xAI) for the four agents.

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Optional local all-MiniLM-L6-v2 semantic copycat matching:
pip install -r requirements-semantic.txt
cp .env.example .env  # fill in BOT_TOKEN, ADMIN_IDS, GROK_API_KEY
python -m bot.main
```

## Deploy on a VPS (systemd)

```bash
sudo mkdir -p /opt/pumpguard-bot
sudo cp -r . /opt/pumpguard-bot
cd /opt/pumpguard-bot
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env  # fill in
sudo cp deploy/pumpguard-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pumpguard-bot
```

Install the optional dashboard dependencies and service when the web view is needed:

```bash
venv/bin/pip install -r requirements-dashboard.txt
sudo cp deploy/pumpguard-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pumpguard-dashboard
```

## Deploy with Docker

```bash
docker compose up -d --build
```

## Deploy on Railway or Render

The deploy buttons above prompt for the three required values: `BOT_TOKEN`, `ADMIN_IDS`, and `GROK_API_KEY`. Both platform definitions mount a persistent volume and set `DB_PATH` to that volume so SQLite data survives deploys. Add any optional variables from `.env.example` after provisioning.

Railway's current project-level Infrastructure as Code definition is `.railway/railway.ts`. To review and apply it manually, install the Railway CLI and run `npm install`, `railway link`, `railway config plan`, then `railway config apply`. Render reads `render.yaml` automatically when the repository is opened as a Blueprint.

## Configuration (`.env`)

| Variable | Description |
|---|---|
| `BOT_TOKEN` | bot token from @BotFather |
| `ADMIN_IDS` | comma-separated admin user IDs |
| `GROK_API_KEY` | xAI API key - used only for the four screening agents |
| `GROK_FAST_MODEL` / `GROK_CHECKER_MODEL` | models for the three cheap agents vs. the adversarial checker |
| `ENABLED_CHAINS` | comma-separated adapter list, only `robinhood` is currently implemented (defaults to `robinhood`) |
| `ROBINHOOD_DATA_URL` / `ROBINHOOD_RPC_URL` | hood.fun public indexer root and Robinhood Chain RPC used for source verification/fallback |
| `MIN_LAUNCH_AGE_SECONDS` / `MIN_UNIQUE_BUYERS` | pre-filter before any Grok call is made |
| `COPYCAT_SIMILARITY_THRESHOLD` | cosine threshold for optional semantic copycat matching (default `0.85`) |
| `MAX_SOL_PER_TRADE` / `DAILY_LOSS_LIMIT_SOL` / `MAX_TRADES_PER_DAY` / `MAX_OPEN_POSITIONS` | risk manager limits |
| `RUG_LOSS_PCT` / `BLOCK_CREATOR_AFTER_RUGS` / `FORGET_CREATORS_AFTER_DAYS` | reputation book tuning |
| `STOP_LOSS_PCT` | real drawdown from entry that force-closes a dry-run position |
| `GROK_BREAKER_FAILURE_THRESHOLD` / `GROK_BREAKER_COOLDOWN_SECONDS` | circuit breaker tuning for Grok outages |
| `ALERT_CHAT_ID` | optional channel/group every passing signal is also posted to |
| `WEBHOOK_URLS` | optional comma-separated webhook endpoints for passing signals, see `docs/webhook-schema.md` |
| `PUBLIC_DIGEST_CHAT_ID` | optional, separate channel for the weekly seven-day performance digest |
| `DASHBOARD_PORT` | read-only dashboard listen port (defaults to `8000`) |
| `NFT_SCREENER_ENABLED` | turns on the second, independent NFT collection screening pipeline (default `false`) |
| `ROBINHOOD_NFT_DATA_URL` | Robinhood Chain NFT marketplace indexer root |
| `NFT_MIN_LAUNCH_AGE_SECONDS` / `NFT_MIN_UNIQUE_MINTERS` | pre-filter before any Grok call is made for a collection |
| `NFT_ALERT_CHAT_ID` | optional separate channel for NFT alerts, falls back to `ALERT_CHAT_ID` |
| `FLOOR_SWEEP_DROP_PCT` / `FLOOR_SWEEP_PUMP_PCT` | percent move from a collection's first-observed floor that triggers a floor-sweep alert |
| `XAI_OAUTH_CLIENT_ID` / `XAI_OAUTH_CLIENT_SECRET` | credentials for an optional xAI OAuth application |
| `XAI_OAUTH_REDIRECT_URI` | public dashboard callback URL, ending in `/oauth/callback` |
| `OAUTH_ENCRYPTION_KEY` | Fernet key used to encrypt OAuth access and refresh tokens at rest |

## Optional Grok account connection

Registering an OAuth application is separate from funding an xAI API account and does not itself buy or consume API credits. Set the four `XAI_OAUTH_*`/`OAUTH_ENCRYPTION_KEY` variables above, register the exact redirect URI with xAI, and expose the dashboard callback over HTTPS. Users can then tap **🔐 Connect Grok account**. The bot stores the short-lived PKCE request for ten minutes, encrypts returned tokens with Fernet, and refreshes an expired access token before an **🔎 Ask Grok** request.

The regular four-agent screening and digest continue to use only `GROK_API_KEY`. User OAuth tokens are used exclusively for the user-triggered second opinion. Dashboard analytics still use a read-only SQLite connection. `/oauth/callback` opens a short-lived writer limited to completing the authorization flow.

## Read-only dashboard

<p align="center">
  <img src="assets/dashboard-mockup.png" alt="Live read-only dashboard" width="100%">
</p>

Run `python -m dashboard.main` or `uvicorn dashboard.main:app`. The dashboard opens the bot's SQLite file with SQLite `mode=ro`. It issues only `SELECT`/`PRAGMA` queries. The bot periodically stores the latest observed price for each open position so `/positions` can display it without starting another PumpPortal connection.

Routes:

- `/` - 1h/24h/7d screening funnel plus recorded backtest metrics
- `/positions` - open dry-run positions and the latest bot-written price snapshot
- `/api/stats` - JSON equivalent of the Telegram statistics view, polled by the dashboard
- `/metrics` - Prometheus text exposition for operational monitoring

**Do not expose analytics routes publicly without authentication in front of them.** If OAuth is enabled, the callback must remain publicly reachable over HTTPS. Configure a reverse proxy that allows `/oauth/callback` while protecting the analytics routes.

## Robinhood Chain data source and pricing

Contributor documentation: [add a new chain or launchpad adapter](docs/adding-a-chain.md).

**Robinhood Chain / hood.fun** polls hood.fun's own read-only `/api/board` indexer every five seconds. Before graduation it calculates the native ETH price from the documented constant-product virtual reserves, `virtualEth / virtualTokens`. After migration it uses `pairPriceWei`, which is sourced from the official Uniswap v3 pool. Robinhood Chain is Arbitrum Orbit chain `4663`. Its public RPC is rate-limited, so production operators should set a dedicated `ROBINHOOD_RPC_URL`, which is intentionally read-only configuration: it provides a stable verification/fallback endpoint without adding wallets, signing, or any live execution path.

hood.fun's indexer does not expose an authoritative unique-buyer count in its launch records, so that one pre-filter is skipped when the adapter reports the value as unavailable. All remaining researcher, agent, checker, risk, and dry-run stages are unchanged.

Semantic copycat detection is local and optional. When `requirements-semantic.txt` is installed, `sentence-transformers/all-MiniLM-L6-v2` is loaded lazily on the first researcher run and compared only with tokens from the same six-hour lookback. If the package or model is unavailable, the bot logs one warning and continues with the existing normalized exact matcher.

## NFT screener (Robinhood Chain)

Set `NFT_SCREENER_ENABLED=true` to run a second, independent screening pipeline alongside the token pipeline, covering new NFT collections on Robinhood Chain. It is architecturally a second source-type behind the same `ChainAdapter`-shaped contract, not a new blockchain - see [add a new chain or launchpad adapter](docs/adding-a-chain.md) for the pattern both follow. hood.fun does not yet document a public NFT marketplace API the way it documents `/api/board` for token launches, so `bot/services/nft/adapter.py` assumes the same request/response shape until a real endpoint is confirmed.

This pipeline is alert-only: an NFT collection has no bonding-curve entry price to dry-run buy/sell against the way a token does, so nothing here is ever fed to `DryRunExecutor`.

- **NFT auditor** (Grok) - flags wash-minting: a collection's supply far exceeding its unique-minter count means a handful of wallets minted most of it themselves
- **NFT narrative** (Grok) - scores hype potential from the collection's name/symbol (no image analysis is wired up yet - see below)
- **Floor-sweep watcher** - tracks each screened collection's floor price against the first value this process observed for it, and alerts on a `FLOOR_SWEEP_DROP_PCT` collapse (possible rug) or a `FLOOR_SWEEP_PUMP_PCT` spike (possible breakout) in either direction
- **Cross-surface signal** - `bot/services/cross_signal.py` checks whether the same creator address already has a launch on the *other* Robinhood surface (a token creator who also deployed an NFT collection, or vice versa) and surfaces it as a flag either pipeline's researcher step can weigh - it says nothing on its own about which way that cuts, a serious builder or a coordinated multi-surface scam both look like this

**Not yet implemented, left as a clearly scoped next step:** real image/art analysis for the narrative agent. `NftCollection` has no image field wired up because this codebase's Grok client only makes text `chat/completions` calls today. Wiring in art hype scoring means passing a collection's artwork to a vision-capable Grok model and is a self-contained addition to `bot/services/nft/agents.py::run_nft_narrative` once prioritized.

## Admin panel

Any user ID in `ADMIN_IDS` sees a "🛠 Admin panel" button on the main menu:

- **📊 Stats** - users, tokens screened, dry-run buys, today's simulated P&L, open positions, blocked creators
- **📈 Backtest** - all-time funnel, win rate, average/median PnL, best/worst trade, and stop-loss hit rate
- **📣 Broadcast** - send a message to every known user
- **📢 Channels** - set or unset the mandatory-subscription channel per interface language

## License

MIT - see [LICENSE](LICENSE).
