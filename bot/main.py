from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.handlers import admin, start
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.services.price_feed import PriceFeed
from bot.services.reputation import ReputationBook
from bot.services.scheduler import run_monitor_loop, run_position_watcher
from bot.services.storage import Storage


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    storage = Storage(config.db_path)
    await storage.connect()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp["storage"] = storage

    subscription_middleware = SubscriptionMiddleware(storage)
    dp.message.outer_middleware(subscription_middleware)
    dp.callback_query.outer_middleware(subscription_middleware)

    dp.include_router(admin.router)
    dp.include_router(start.router)

    reputation = ReputationBook(storage)
    price_feed = PriceFeed()
    price_feed_task = asyncio.create_task(price_feed.run())
    monitor_task = asyncio.create_task(run_monitor_loop(bot, storage, price_feed))
    watcher_task = asyncio.create_task(run_position_watcher(storage, reputation, price_feed))

    try:
        await dp.start_polling(bot)
    finally:
        price_feed_task.cancel()
        monitor_task.cancel()
        watcher_task.cancel()
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
