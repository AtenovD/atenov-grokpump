from __future__ import annotations

import os
import tempfile
import time
import unittest

import aiosqlite
from starlette.requests import Request

from bot.services.storage import Position, Storage
from dashboard.main import create_app
from dashboard.queries import read_backtest, read_funnel, read_open_positions, read_stats


class DashboardTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_database_renders_every_endpoint(self) -> None:
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        path = handle.name
        handle.close()
        try:
            app = create_app(path)
            async with app.router.lifespan_context(app):
                for route_path in ("/", "/positions", "/api/stats"):
                    route = next(route for route in app.routes if route.path == route_path)
                    request = Request({
                        "type": "http", "app": app, "method": "GET", "path": route_path,
                        "headers": [], "query_string": b"",
                    })
                    response = (
                        await route.endpoint(request, "24h")
                        if route_path == "/" else await route.endpoint(request)
                    )
                    if hasattr(response, "body"):
                        self.assertTrue(response.body)
                self.assertEqual((await read_stats(app.state.storage))["screened_24h"], 0)
                self.assertEqual(await read_funnel(app.state.storage, 3600), [])
                self.assertEqual((await read_backtest(app.state.storage, 3600))["total_signals"], 0)
                self.assertEqual(await read_open_positions(app.state.storage), [])
                with self.assertRaises(aiosqlite.OperationalError):
                    await app.state.storage.db.execute("CREATE TABLE forbidden (id INTEGER)")
        finally:
            os.unlink(path)

    async def test_positions_use_bot_written_price_snapshot(self) -> None:
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        path = handle.name
        handle.close()
        try:
            writer = Storage(path)
            await writer.connect()
            await writer.open_position(
                Position("mint", "TKN", 1.0, 0.1, 0.8, "creator", int(time.time()), "open")
            )
            await writer.record_price_snapshot("mint", 1.25)
            await writer.log_signal("mint", "TKN", 0.8, "executor", "bought")
            await writer.close()

            reader = Storage(path)
            await reader.connect_readonly()
            positions = await read_open_positions(reader)
            self.assertEqual(len(positions), 1)
            self.assertEqual(positions[0]["chain"], "solana")
            self.assertEqual(positions[0]["current_price"], 1.25)
            self.assertEqual((await read_stats(reader))["bought_24h"], 1)
            await reader.close()
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
