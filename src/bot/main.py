"""Main bot entry point."""

import asyncio
import logging
import signal

from aiogram import Dispatcher

from src.bot.config import create_bot, create_dispatcher, on_startup, on_shutdown, setup_routers
from src.core.database import init_db
from src.core.logging import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main bot runner."""
    # Setup logging
    setup_logging("INFO")

    # Create bot and dispatcher
    bot = create_bot()
    dispatcher = create_dispatcher()

    # Setup routers
    root_router = setup_routers()
    dispatcher.include_router(root_router)

    # Register startup/shutdown handlers
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Setup graceful shutdown
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_signal():
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    try:
        # Start polling
        logger.info("Bot starting...")
        await dispatcher.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await dispatcher.shutdown()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
