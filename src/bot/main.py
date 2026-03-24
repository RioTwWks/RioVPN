"""Main bot entry point."""

import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher

from src.bot.config import create_bot, create_dispatcher, on_startup, on_shutdown, setup_routers
from src.bot.notifications import init_notifications
from src.core.database import init_db
from src.core.logging import setup_logging
from src.workers.scheduler import create_scheduler

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

    # Initialize notifications
    notification_service = init_notifications(bot)
    logger.info("Notification service initialized")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start scheduler
    scheduler = create_scheduler(bot=bot)
    scheduler.start()
    logger.info("Background scheduler started")

    # Register startup/shutdown handlers
    async def on_startup_wrapper(disp: Dispatcher, b: Bot) -> None:
        await on_startup(disp, b)

    async def on_shutdown_wrapper(disp: Dispatcher, b: Bot) -> None:
        scheduler.stop()
        await on_shutdown(disp, b)

    dispatcher.startup.register(on_startup_wrapper)
    dispatcher.shutdown.register(on_shutdown_wrapper)

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
        scheduler.stop()
        await dispatcher.shutdown()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
