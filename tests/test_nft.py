from __future__ import annotations

import os
import time
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BOT_TOKEN", "test-token")

import aiohttp

from bot.services.cross_signal import cross_surface_note
from bot.services.models import AgentVerdict, NftCollection
from bot.services.nft.adapter import RobinhoodNftAdapter
from bot.services.nft.pipeline import _code_filter, screen_collection
from bot.services.reputation import ReputationBook
from bot.services.storage import Storage


def _collection(**overrides) -> NftCollection:
    defaults = dict(
        address="0xnft",
        name="Cool Collection",
        symbol="COOL",
        creator="0xcreator",
        supply=1000,
        unique_minters=50,
        created_at=time.time() - 120,
    )
    defaults.update(overrides)
    return NftCollection(**defaults)


class CrossSignalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.storage = Storage(":memory:")
        await self.storage.connect()

    async def asyncTearDown(self) -> None:
        await self.storage.close()

    async def test_no_note_when_creator_only_on_one_surface(self) -> None:
        await self.storage.mark_seen("0xtoken", "TKN", "Token", "robinhood", "0xcreator")
        note = await cross_surface_note(self.storage, "0xcreator", "robinhood")
        self.assertIsNone(note)

    async def test_note_when_creator_appears_on_both_surfaces(self) -> None:
        await self.storage.mark_seen("0xtoken", "TKN", "Token", "robinhood", "0xcreator")
        await self.storage.mark_seen("0xnft", "NFT", "Collection", "robinhood-nft", "0xcreator")

        note_from_token_side = await cross_surface_note(self.storage, "0xcreator", "robinhood")
        note_from_nft_side = await cross_surface_note(self.storage, "0xcreator", "robinhood-nft")

        self.assertIsNotNone(note_from_token_side)
        self.assertIn("NFT collection", note_from_token_side)
        self.assertIsNotNone(note_from_nft_side)
        self.assertIn("token", note_from_nft_side)

    async def test_no_creator_is_a_no_op(self) -> None:
        self.assertIsNone(await cross_surface_note(self.storage, None, "robinhood"))


class RobinhoodNftAdapterTests(unittest.IsolatedAsyncioTestCase):
    def test_floor_price_parses_wei(self) -> None:
        price = RobinhoodNftAdapter._floor_price({"floorPriceWei": str(2 * 10**17)})
        self.assertAlmostEqual(price, 0.2)

    def test_floor_price_missing_is_none(self) -> None:
        self.assertIsNone(RobinhoodNftAdapter._floor_price({}))
        self.assertIsNone(RobinhoodNftAdapter._floor_price({"floorPriceWei": "0"}))

    async def test_baseline_poll_emits_nothing_new(self) -> None:
        adapter = RobinhoodNftAdapter("https://example.test", poll_interval=0)
        items = [{"address": "0xexisting", "name": "Old", "symbol": "OLD", "timestamp": 1}]

        async def fake_sleep(_seconds: float) -> None:
            raise _StopLoop()

        collected = []
        with patch.object(adapter, "_fetch", AsyncMock(return_value=items)), \
             patch("bot.services.nft.adapter.asyncio.sleep", fake_sleep):
            with self.assertRaises(_StopLoop):
                async for collection in adapter.stream_new_collections():
                    collected.append(collection)
        self.assertEqual(collected, [])

    async def test_genuinely_new_collection_after_baseline_is_emitted_once(self) -> None:
        adapter = RobinhoodNftAdapter("https://example.test", poll_interval=0)
        baseline_items = [{"address": "0xold", "timestamp": 1}]
        new_items = [
            {"address": "0xold", "timestamp": 1},
            {
                "address": "0xNEW", "name": "New Drop", "symbol": "NEW", "creator": "0xc",
                "supply": 500, "uniqueMinters": 20, "timestamp": 2, "floorPriceWei": str(10**17),
            },
        ]
        poll_count = 0

        async def fake_sleep(_seconds: float) -> None:
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 2:
                raise _StopLoop()

        collected = []
        with patch.object(adapter, "_fetch", AsyncMock(side_effect=[baseline_items, new_items])), \
             patch("bot.services.nft.adapter.asyncio.sleep", fake_sleep):
            with self.assertRaises(_StopLoop):
                async for collection in adapter.stream_new_collections():
                    collected.append(collection)
        self.assertEqual(len(collected), 1)
        self.assertEqual(collected[0].address, "0xnew")
        self.assertEqual(collected[0].floor_price, 0.1)

    def test_watch_unwatch_and_floor_lookup(self) -> None:
        adapter = RobinhoodNftAdapter("https://example.test")
        adapter.watch("0xABC")
        self.assertIn("0xabc", adapter.watched_addresses())
        adapter._update_floors([{"address": "0xabc", "floorPriceWei": str(5 * 10**17)}])
        self.assertAlmostEqual(adapter.get_floor_price("0xABC"), 0.5)
        adapter.unwatch("0xabc")
        self.assertIsNone(adapter.get_floor_price("0xabc"))
        self.assertNotIn("0xabc", adapter.watched_addresses())


class _StopLoop(Exception):
    """Breaks out of the adapter's otherwise-infinite polling loop in tests."""


class NftPipelineFilterTests(unittest.IsolatedAsyncioTestCase):
    def test_code_filter_rejects_too_few_minters(self) -> None:
        self.assertEqual(_code_filter(_collection(unique_minters=1)), "too_few_minters")

    def test_code_filter_rejects_too_young(self) -> None:
        self.assertEqual(_code_filter(_collection(created_at=time.time())), "too_young")

    def test_code_filter_passes_clean_collection(self) -> None:
        self.assertIsNone(_code_filter(_collection()))

    async def test_screen_collection_skips_below_threshold(self) -> None:
        storage = Storage(":memory:")
        await storage.connect()
        rejected = AgentVerdict("nft_auditor", 0.1, "suspicious", approve=False)
        with patch(
            "bot.services.nft.pipeline.nft_agents.run_nft_auditor", AsyncMock(return_value=rejected)
        ), patch(
            "bot.services.nft.pipeline.nft_agents.run_nft_narrative", AsyncMock(return_value=rejected)
        ):
            async with aiohttp.ClientSession() as session:
                result = await screen_collection(session, storage, ReputationBook(storage), _collection())
        self.assertIsNone(result)
        await storage.close()

    async def test_screen_collection_passes_clean_collection(self) -> None:
        storage = Storage(":memory:")
        await storage.connect()
        passed = AgentVerdict("nft_auditor", 0.9, "clean", approve=True)
        with patch(
            "bot.services.nft.pipeline.nft_agents.run_nft_auditor", AsyncMock(return_value=passed)
        ), patch(
            "bot.services.nft.pipeline.nft_agents.run_nft_narrative", AsyncMock(return_value=passed)
        ):
            async with aiohttp.ClientSession() as session:
                result = await screen_collection(session, storage, ReputationBook(storage), _collection())
        self.assertIsNotNone(result)
        self.assertEqual(result.total_score, 0.9)
        await storage.close()


if __name__ == "__main__":
    unittest.main()
