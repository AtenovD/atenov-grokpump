# Adding a launchpad or chain adapter

PumpGuard isolates every market-data integration behind `ChainAdapter` in `bot/services/chains/__init__.py`. A fourth integration should only need an adapter module, configuration fields, one factory entry, a token URL/label, and focused tests. The screening, reputation, risk, dry-run execution, position watcher, backtest, and dashboard already scope identity by `(chain, mint)`.

This guide uses `example` as the new stable chain ID. Replace it with a short lowercase identifier that will not need to change later: it is persisted in SQLite and appears in webhooks and metrics.

## 1. Understand the contract

An adapter implements this structural protocol:

```python
class ChainAdapter(Protocol):
    chain_id: str

    def stream_new_tokens(self) -> AsyncIterator[Token]: ...
    def watch(self, mint: str) -> None: ...
    def unwatch(self, mint: str) -> None: ...
    def get_price(self, mint: str) -> float | None: ...
    async def run(self) -> None: ...
```

There are two independent long-running data paths:

1. `stream_new_tokens()` discovers launches and yields each launch once. The scheduler consumes it and runs the screening pipeline.
2. `run()` refreshes prices for addresses registered by `watch()`. The position watcher calls `get_price()` and enforces the simulated stop-loss. `unwatch()` releases closed positions.

Both paths are started by `bot/main.py`. They must reconnect forever after expected network failures. They must not create wallets, sign messages, submit transactions, or depend on private keys: PumpGuard is deliberately dry-run only.

## 2. Map the launchpad data to `Token`

`bot/services/models.py` defines the canonical launch record:

| Field | Required meaning |
|---|---|
| `mint` | Canonical token contract/address. Normalize case consistently for case-insensitive chains. |
| `symbol`, `name` | Untrusted display strings, or `None`. Do not interpret them as commands. |
| `creator` | Creator/deployer address if authoritative, otherwise `None`. |
| `sol_in_curve` | Legacy field name for observed native liquidity/curve funding. Preserve native-unit consistency within the adapter. |
| `unique_buyers` | Authoritative unique buyer count, or `None` when the source does not provide it. Never invent a count. |
| `created_at` | UTC Unix timestamp in seconds. Parse source timestamps explicitly. |
| `chain` | Exactly the adapter's stable `chain_id`. |
| `reference_price` | Real, positive entry price in the adapter's pricing unit, when available. |

For a non-Solana adapter, provide `reference_price`. `DryRunExecutor` retains a legacy pump.fun fallback based on `sol_in_curve` and `unique_buyers`; that fallback is not a meaningful EVM or arbitrary-chain price. Do not yield a launch until the source exposes a positive curve or pool price.

Use authoritative launchpad/indexer fields and document their units. Avoid float arithmetic on raw integer reserve values until after parsing both values. Reject zero/negative reserves and malformed addresses rather than manufacturing a price.

## 3. Choose the closest existing example

- `solana.py` is the WebSocket pattern. It has one subscription for launch discovery and another dynamic subscription for watched-token trades. `_want_resubscribe` rebuilds the trade subscription when the watched set changes. Its pre-graduation price is derived from reported virtual reserves.
- `base.py` is a REST polling pattern. It establishes a baseline on its first response so a restart does not emit the entire current catalogue as new. It reads Clanker's pool-derived USD price and normalizes EVM addresses to lowercase.
- `robinhood.py` is a hybrid curve/pool pricing example. Before graduation it derives price from `virtualEth / virtualTokens`; after migration it prefers the indexed Uniswap-pair price. It also establishes a first-poll baseline.

Copy structure, not source-specific field names. Confirm the new launchpad's API contract and rate limits from primary documentation before implementation.

## 4. Implement the adapter

Create `bot/services/chains/example.py`. A minimal polling adapter looks like this:

```python
from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator

import aiohttp

from bot.services.models import Token


class ExampleAdapter:
    chain_id = "example"

    def __init__(self, data_url: str, rpc_url: str, poll_interval: float = 5.0) -> None:
        self.data_url = data_url.rstrip("/")
        self.rpc_url = rpc_url
        self.poll_interval = poll_interval
        self._watched: set[str] = set()
        self._prices: dict[str, float] = {}
        self._baseline: set[str] | None = None
        self._emitted: set[str] = set()

    @staticmethod
    def _key(address: str) -> str:
        return address.lower()  # Use the chain's canonical normalization rule.

    async def _fetch(self, session: aiohttp.ClientSession) -> list[dict]:
        async with session.get(
            f"{self.data_url}/launches",
            timeout=aiohttp.ClientTimeout(total=20),
        ) as response:
            response.raise_for_status()
            payload = await response.json()
        return payload["items"]

    @staticmethod
    def _price(item: dict) -> float | None:
        value = float(item.get("price") or 0)
        return value if value > 0 else None

    def _update_prices(self, items: list[dict]) -> None:
        for item in items:
            address = item.get("address")
            price = self._price(item)
            if address and self._key(address) in self._watched and price is not None:
                self._prices[self._key(address)] = price

    async def stream_new_tokens(self) -> AsyncIterator[Token]:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    items = await self._fetch(session)
                    self._update_prices(items)
                    current = {self._key(x["address"]) for x in items if x.get("address")}
                    if self._baseline is None:
                        self._baseline = current
                    else:
                        for item in reversed(items):
                            address = item.get("address")
                            key = self._key(address) if address else ""
                            price = self._price(item)
                            if not key or key in self._baseline or key in self._emitted or price is None:
                                continue
                            self._emitted.add(key)
                            yield Token(
                                mint=key,
                                symbol=item.get("symbol"),
                                name=item.get("name"),
                                creator=item.get("creator"),
                                sol_in_curve=float(item.get("nativeLiquidity") or 0),
                                unique_buyers=item.get("uniqueBuyers"),
                                created_at=float(item.get("createdAt") or time.time()),
                                chain=self.chain_id,
                                reference_price=price,
                            )
                except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, TypeError, ValueError):
                    # Log the exception in production code; expected source failures reconnect.
                    pass
                await asyncio.sleep(self.poll_interval)

    def watch(self, mint: str) -> None:
        self._watched.add(self._key(mint))

    def unwatch(self, mint: str) -> None:
        key = self._key(mint)
        self._watched.discard(key)
        self._prices.pop(key, None)

    def get_price(self, mint: str) -> float | None:
        return self._prices.get(self._key(mint))

    async def run(self) -> None:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    self._update_prices(await self._fetch(session))
                except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, TypeError, ValueError):
                    pass
                await asyncio.sleep(self.poll_interval)
```

Production code should log the caught exception with source context, as all three existing adapters do. Catch expected transport/parsing failures narrowly. Do not use a bare `except`, and let `asyncio.CancelledError` propagate so shutdown works.

Keep the polling interval outside the per-item loop. Respect server rate limits and use one `ClientSession` per long-running method, not one session per request. Bound every request with a timeout.

## 5. Register configuration and presentation

Add source fields to `Config` in `bot/config.py`, with safe read-only public defaults only when a stable official endpoint exists:

```python
example_data_url: str = field(
    default_factory=lambda: os.getenv("EXAMPLE_DATA_URL", "https://indexer.example/api")
)
example_rpc_url: str = field(
    default_factory=lambda: os.getenv("EXAMPLE_RPC_URL", "https://rpc.example")
)
```

Then update `bot/services/chains/__init__.py`:

1. Add `"example": "🟠 Example"` to `CHAIN_LABELS`.
2. Add a correct explorer/launchpad branch to `token_url()`. Do not let a new chain fall through to another chain's URL.
3. Import `ExampleAdapter` inside `build_adapters()`.
4. Add `"example": lambda: ExampleAdapter(config.example_data_url, config.example_rpc_url)` to `factories`.

Add `EXAMPLE_DATA_URL` and `EXAMPLE_RPC_URL` to `.env.example` and the README configuration table. Operators enable it with:

```dotenv
ENABLED_CHAINS=solana,example
```

Unknown names intentionally fail fast in `build_adapters()` rather than silently leaving a requested chain unmonitored.

## 6. Verify persistence and pipeline behavior

Do not add chain-specific tables. Existing storage APIs accept `chain` and use composite keys for seen tokens, creators, positions, price snapshots, and signals. Always pass `token.chain` when calling them. The shared scheduler already does this.

Add tests in `tests/test_multichain.py` or a dedicated `tests/test_example_chain.py` covering at least:

- source payload to `Token` parsing, including timestamp and address normalization;
- curve and post-graduation price calculations with known fixtures;
- zero/invalid price rejection;
- first-poll baseline behavior (old catalogue entries are not emitted);
- a genuinely new launch is emitted exactly once;
- `watch()` → refresh → `get_price()` → `unwatch()`;
- recovery after a mocked timeout/non-2xx response;
- the same address on two different chains remains distinct in dedup, reputation, positions, and signals;
- a passing token stores the new `chain_id` through `screen_token()`.

Never call a real network endpoint in tests. Extract pure `_price`, timestamp, and payload parsing helpers, and mock `_fetch()` or the HTTP session for loop behavior.

Run the repository checks:

```bash
python -m py_compile $(find bot -type f -name '*.py' -print)
python -m unittest discover -v
```

Finally, run a staging instance long enough to observe reconnects and prices. Confirm that an open dry-run position gets fresh `price_snapshots`, the dashboard shows the same chain/address, and stop-loss calculations use the same price unit as entry.

## Review checklist

- [ ] `chain_id` is stable, lowercase, and registered in the factory, label, and URL helper.
- [ ] Discovery emits only new launches, once, after a real positive entry price exists.
- [ ] Address normalization is identical in discovery, watch, unwatch, and price lookup.
- [ ] `created_at`, reserve units, and price units are documented and tested.
- [ ] Missing buyer data is `None`, not a fabricated value.
- [ ] Both long-running paths reconnect with bounded requests and cancellable sleeps.
- [ ] No wallet, secret key, signing, approval, swap, or transaction-broadcasting code was added.
- [ ] All storage and pipeline calls preserve the chain dimension.
- [ ] Unit tests are deterministic and offline.
- [ ] `.env.example`, README, and source attribution are updated.
