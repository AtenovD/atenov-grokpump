# PumpGuard / GrokPump — Roadmap

Full list of what's shipped, what's queued, and how each remaining item helps either **reach**
(stars, users, credibility) or **money** (a real path to revenue). Nothing below requires the
project owner to personally run or operate the bot.

## ✅ Already shipped

- Core pipeline: Researcher (free DB lookups) → Auditor/Narrative/Timing (Grok, parallel) → Checker
  (adversarial, stronger model) → Risk manager (5 arithmetic limits) → dry-run buy
- Real bonding-curve price tracking + real stop-loss exits (replaced the earlier random-outcome bug)
- Circuit breaker on Grok calls, prompt-injection sanitization on token metadata, Grok-synthesized
  explainability digest per signal
- Button-only RU/EN Telegram frontend, mandatory-subscription gate, admin panel
- Three PRs open against `main` (not yet merged): backtest engine, multi-chain support
  (Solana/pump.fun + Base/Clanker + Robinhood Chain/hood.fun), read-only web dashboard

## 🔧 Technical additions worth building next

| # | Item | Why it matters |
|---|---|---|
| 1 | **"Sign in with xAI" (OAuth 2.0 PKCE)** | Lets each *user* of the bot connect their own SuperGrok/X Premium+ subscription for a personal "ask Grok about this token" feature, instead of burning the operator's shared API key. Real, existing xAI feature (launched May 2026, `accounts.x.ai`). Blocked only on registering an OAuth app in the xAI console — no paid API credits needed just to register it, unlike using the API itself. |
| 2 | Semantic (embedding-based) copycat detection | Current copycat check is exact-name match. Swapping in a small local embedding model catches near-duplicates ("PEPE 2.0" vs "Pepe2.0") — meaningfully better fraud detection, good talking point. |
| 3 | CI on GitHub Actions (lint + tests on every PR) | Repos with a green CI badge get taken far more seriously by anyone evaluating whether to star/fork/deploy it. Cheap to add, first thing a technical evaluator checks. |
| 4 | One-click deploy buttons (Railway / Render / Fly.io) | The single biggest lever for adoption — turns "clone, configure five env vars, run Docker" into "click a button." Directly drives GitHub traffic and stars. |
| 5 | Public webhook/API export of signals | Turns the project from "a bot" into "a platform other developers build on" — a JSON webhook other bots/dashboards can subscribe to. This is also the seed of a paid API tier (see monetization below). |
| 6 | Public read-only demo signal channel | A free, running, public Telegram channel posting real (dry-run) signals is the single best piece of marketing this project can have — visible proof it works, linkable from the README. |
| 7 | Auto-posted weekly backtest report | Once the backtest engine (PR #1) is merged, have it auto-post its report to the public demo channel weekly — recurring, self-generating content and a running credibility track record. |
| 8 | More chains via the existing `ChainAdapter` protocol | The multi-chain PR already defines a clean plugin interface — document "how to add a chain" and treat new chains as community contributions instead of work the owner has to do. |
| 9 | Prometheus/Grafana metrics export | Attracts more serious self-hosters and small teams evaluating it for internal use — a normal expectation for infra-adjacent tools. |
| 10 | Rate-limited public API tier | Natural extension of #5 — a paid tier for higher rate limits is a direct, simple revenue stream once the free webhook exists. |

## 📣 Reach / visibility (non-code)

- Polished README hero: short GIF or screenshot sequence of a real signal + the admin panel
- Submit to relevant curated lists (awesome-telegram-bots, awesome-crypto-tools, any "awesome-grok"
  list — the earlier repo research in this project found several already active)
- "Show HN" / Product Hunt / relevant subreddit and Discord launch posts once the demo channel (item 6) is live and has some running history
- Standard badges: license, stars, build status, "Powered by Grok"
- A short X/Twitter thread walking through one real signal end-to-end (screenshot-driven, no code required to produce)

## 💰 Monetization paths specific to this project

1. **Hosted SaaS** — user connects their own Telegram channel + Grok key + RPC endpoint, pays a
   monthly fee for a managed instance instead of self-hosting.
2. **Premium signal channel** — the free demo channel (item 6) stays free; a second, curated/faster
   channel is paid (Telegram Stars native paid channels, or external billing).
3. **Sponsored mentions** — clearly labeled sponsor slots in the signal channel, sold to tool/project
   vendors — monetizes the audience, not the software.
4. **Data licensing** — the backtest engine's historical accuracy data is a real, sellable asset for
   funds/researchers once enough history has accumulated.
5. **White-label deployment service** — flat one-time fee to configure and deploy a branded instance
   for another community/server; zero ongoing hosting obligation for the seller.
6. **Paid "Pro" tier** — gates item #1 (personal Grok via OAuth), custom risk profiles, and extra
   chains behind a one-time or subscription unlock on top of the free open-source core.
7. **Consulting/custom builds** — the multi-chain `ChainAdapter` pattern and the whole pipeline
   architecture are reusable for adjacent paid engagements (e.g. a similar screener for a different
   asset class).

## Practical checklist (not urgent, doesn't require active involvement)

- [ ] Merge PR #1 (backtest), #2 (multi-chain), #3 (dashboard) into `main`
- [ ] Fund a `GROK_API_KEY` (even a small balance covers a lot on the fast model) to unlock live
      testing — separate from and unrelated to item #1's OAuth registration, which doesn't need
      a funded balance to set up
- [ ] Rotate/replace any previously exposed credentials (bot token, GitHub PAT)
- [ ] Deploy the demo instance (item 6) somewhere persistent once ready to launch publicly
