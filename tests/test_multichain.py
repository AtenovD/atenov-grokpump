from __future__ import annotations

import os
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BOT_TOKEN", "test-token")

import aiohttp

from bot.services.agents import run_researcher
from bot.services.chains.robinhood import RobinhoodAdapter
from bot.services.executor import DryRunExecutor
from bot.services.models import AgentVerdict, Token
from bot.services.pipeline import screen_token
from bot.services.reputation import ReputationBook
from bot.services.risk import RiskManager
from bot.services.storage import Position, Storage


class MultiChainStorageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.storage = Storage(":memory:")
        await self.storage.connect()

    async def asyncTearDown(self) -> None:
        await self.storage.close()

    async def test_same_creator_is_scoped_per_chain(self) -> None:
        address = "same-address"
        await self.storage.record_creator_outcome(address, True, "solana")
        reputation = ReputationBook(self.storage)

        self.assertIsNotNone(await reputation.is_blocked(address, "solana"))
        self.assertIsNone(await reputation.is_blocked(address, "base"))

    async def test_dedup_copycats_and_positions_are_scoped_per_chain(self) -> None:
        address = "same-address"
        await self.storage.mark_seen("same-mint", "SAME", "Same", "solana")
        self.assertTrue(await self.storage.is_seen("same-mint", "solana"))
        self.assertFalse(await self.storage.is_seen("same-mint", "base"))
        await self.storage.mark_seen("same-mint", "SAME", "Same", "base")

        base_token = Token("new", "SAME", "Same", "creator", 1, 5, time.time(), "base")
        solana_token = Token("new", "SAME", "Same", "creator", 1, 5, time.time(), "solana")
        self.assertIn("possible_copycat", (await run_researcher(self.storage, base_token)).flags)
        self.assertIn("possible_copycat", (await run_researcher(self.storage, solana_token)).flags)

        base_position = Position("same-mint", "BASE", 1, 0.1, 0.8, address, 1, "open", "base")
        sol_position = Position("same-mint", "SOL", 1, 0.1, 0.8, address, 1, "open", "solana")
        await self.storage.open_position(base_position)
        await self.storage.open_position(sol_position)
        self.assertEqual(len(await self.storage.open_positions()), 2)

    async def test_robinhood_virtual_reserve_price(self) -> None:
        price = RobinhoodAdapter._price(
            {"curve": {"virtualEth": str(3 * 10**18), "virtualTokens": str(10**27)}}
        )
        self.assertAlmostEqual(price, 3e-9)

    async def test_pipeline_persists_chain(self) -> None:
        token = Token(
            "0xbase", "BASE", "Base Token", "creator", 1, 5,
            time.time() - 120, "base", 0.001,
        )
        passed = AgentVerdict("mock", 0.9, "ok", approve=True)
        with patch(
            "bot.services.pipeline.agents.run_auditor", AsyncMock(return_value=passed)
        ), patch(
            "bot.services.pipeline.agents.run_narrative", AsyncMock(return_value=passed)
        ), patch(
            "bot.services.pipeline.agents.run_timing", AsyncMock(return_value=passed)
        ), patch(
            "bot.services.pipeline.agents.run_checker", AsyncMock(return_value=passed)
        ):
            async with aiohttp.ClientSession() as session:
                result = await screen_token(
                    session, self.storage, RiskManager(self.storage),
                    ReputationBook(self.storage), DryRunExecutor(), token, {},
                )
        self.assertIsNotNone(result)
        self.assertEqual((await self.storage.open_positions())[0].chain, "base")
        cursor = await self.storage.db.execute(
            "SELECT chain FROM signals WHERE mint = ?", (token.mint,)
        )
        self.assertEqual((await cursor.fetchone())[0], "base")
        self.assertIn("base: 1", (await self.storage.stats())["chains_24h"])


class MigrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_old_database_rows_migrate_to_solana(self) -> None:
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        path = handle.name
        handle.close()
        try:
            connection = sqlite3.connect(path)
            connection.executescript(
                """
                CREATE TABLE seen_tokens (mint TEXT PRIMARY KEY, symbol TEXT, name TEXT, first_seen_at INTEGER NOT NULL);
                CREATE TABLE creators (creator TEXT PRIMARY KEY, rugs INTEGER NOT NULL DEFAULT 0, wins INTEGER NOT NULL DEFAULT 0, last_seen_at INTEGER NOT NULL);
                CREATE TABLE positions (mint TEXT PRIMARY KEY, symbol TEXT, entry_price REAL NOT NULL, sol_spent REAL NOT NULL, score REAL NOT NULL, creator TEXT, opened_at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'open');
                CREATE TABLE signals (id INTEGER PRIMARY KEY AUTOINCREMENT, mint TEXT NOT NULL, symbol TEXT, score REAL, stage TEXT NOT NULL, outcome TEXT NOT NULL, detail TEXT, created_at INTEGER NOT NULL);
                INSERT INTO seen_tokens VALUES ('legacy', 'OLD', 'Old', 1);
                INSERT INTO creators VALUES ('creator', 1, 0, 1);
                INSERT INTO positions VALUES ('legacy', 'OLD', 1, 0.1, 0.8, 'creator', 1, 'open');
                INSERT INTO signals (mint, symbol, score, stage, outcome, detail, created_at) VALUES ('legacy', 'OLD', 0.8, 'executor', 'bought', '', 1);
                """
            )
            connection.commit()
            connection.close()

            storage = Storage(path)
            await storage.connect()
            self.assertTrue(await storage.is_seen("legacy", "solana"))
            self.assertEqual(await storage.creator_rugs("creator", "solana"), 1)
            self.assertEqual((await storage.open_positions())[0].chain, "solana")
            cursor = await storage.db.execute("SELECT chain FROM signals WHERE mint = 'legacy'")
            self.assertEqual((await cursor.fetchone())[0], "solana")
            await storage.close()
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
