<p align="center">
  <img src="assets/pipeline-banner.svg" alt="PumpGuard Bot screening pipeline" width="100%">
</p>

<h1 align="center">PumpGuard Bot</h1>

<p align="center">
  A Telegram bot that screens new pump.fun token launches through four Grok-powered agents, a risk manager, and a creator reputation book — then simulates the trade. No live execution, ever.
</p>

<p align="center">
  <img src="assets/chat-preview.svg" alt="PumpGuard Bot chat preview" width="100%">
</p>

## ⚠️ What this is and isn't

This is a **research/screening tool**, not a trading bot. Every "buy" and "sell" is simulated (dry-run): no wallet, no signing, no on-chain transaction. Bonding-curve memecoins on pump.fun routinely lose their entire value; nothing here is financial advice, and there is no live executor to wire up — that's a deliberately different, much higher-stakes piece of software that this project does not include.

## Features

- **New-launch monitor** — subscribes to [PumpPortal](https://pumpportal.fun)'s public pump.fun WebSocket feed, filters by age and buyer count before spending a single Grok call
- **Four Grok agents**, run in sequence, cheapest first:
  - **Auditor** — looks for wash trading / bundled buys in the trade and holder data
  - **Narrative** — scores the meme's attention potential from its name/symbol
  - **Timing** — judges the current window using only this bot's own observed launch/outcome rate (no external price feeds)
  - **Checker** — an adversarial final pass on a stronger model, given the other three verdicts, explicitly looking for a reason to reject
- **Risk manager** — five independent limits: max SOL per trade, daily loss limit, max trades/day, max open positions, stop-loss — pure arithmetic, no model involved, and the last gate before a (simulated) trade
- **Reputation book** — creators are blocked after their tracked launches rug, forgotten after a configurable number of days
- **Dry-run executor** — simulates entry/exit prices and P&L, feeding the reputation book and daily counters exactly like a live executor would
- **Button-only Telegram frontend**: RU/EN language picker, stats, open positions, optional mandatory-subscription gate, button-driven admin panel — no slash commands beyond `/start`

## Stack

Python 3.12, [aiogram 3](https://docs.aiogram.dev/), aiohttp, `websockets`, aiosqlite. Grok API (xAI) for the four agents.

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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

## Deploy with Docker

```bash
docker compose up -d --build
```

## Configuration (`.env`)

| Variable | Description |
|---|---|
| `BOT_TOKEN` | bot token from @BotFather |
| `ADMIN_IDS` | comma-separated admin user IDs |
| `GROK_API_KEY` | xAI API key — used only for the four screening agents |
| `GROK_FAST_MODEL` / `GROK_CHECKER_MODEL` | models for the three cheap agents vs. the adversarial checker |
| `DATA_WS_URL` | pump.fun launch feed (defaults to PumpPortal's public endpoint) |
| `MIN_LAUNCH_AGE_SECONDS` / `MIN_UNIQUE_BUYERS` | pre-filter before any Grok call is made |
| `MAX_SOL_PER_TRADE` / `DAILY_LOSS_LIMIT_SOL` / `MAX_TRADES_PER_DAY` / `MAX_OPEN_POSITIONS` | risk manager limits |
| `RUG_LOSS_PCT` / `BLOCK_CREATOR_AFTER_RUGS` / `FORGET_CREATORS_AFTER_DAYS` | reputation book tuning |
| `ALERT_CHAT_ID` | optional channel/group every passing signal is also posted to |

## Admin panel

Any user ID in `ADMIN_IDS` sees a "🛠 Admin panel" button on the main menu:

- **📊 Stats** — users, tokens screened, dry-run buys, today's simulated P&L, open positions, blocked creators
- **📣 Broadcast** — send a message to every known user
- **📢 Channels** — set or unset the mandatory-subscription channel per interface language

## License

MIT — see [LICENSE](LICENSE).
