"""Main bot entry point."""

import asyncio
import logging
import signal
from typing import Optional

from aiogram import Bot, Dispatcher

from src.bot.config import create_bot, create_dispatcher, on_startup, on_shutdown, setup_routers
from src.bot.notifications import init_notifications
from src.core.config import settings
from src.core.database import init_db
from src.core.logging import setup_logging
from src.workers.scheduler import create_scheduler

logger = logging.getLogger(__name__)

# Global references for cleanup
_bot: Optional[Bot] = None
_scheduler = None


async def cleanup() -> None:
    """
    Perform cleanup on shutdown.

    Closes database connections, stops scheduler, and cleans up bot session.
    """
    logger.info("Starting cleanup...")

    # Stop scheduler
    if _scheduler:
        _scheduler.stop()
        logger.info("Scheduler stopped")

    # Close bot session
    if _bot:
        await _bot.session.close()
        logger.info("Bot session closed")

    # Dispose database engine
    from src.core.database import engine

    await engine.dispose()
    logger.info("Database engine disposed")

    logger.info("Cleanup completed")


async def main() -> None:
    """Main bot runner."""
    global _bot, _scheduler

    # Setup logging with config
    setup_logging(
        level=settings.log_level,
        log_dir=settings.log_dir,
    )

    # Create bot and dispatcher
    _bot = create_bot()
    dispatcher = create_dispatcher()

    # Setup routers
    root_router = setup_routers()
    dispatcher.include_router(root_router)

    # Initialize notifications
    notification_service = init_notifications(_bot)
    logger.info("Notification service initialized")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start scheduler
    _scheduler = create_scheduler(bot=_bot)
    _scheduler.start()
    logger.info("Background scheduler started")

    # Register startup/shutdown handlers
    async def on_startup_wrapper(bot: Bot) -> None:
        await on_startup(None, bot)

    async def on_shutdown_wrapper(bot: Bot) -> None:
        _scheduler.stop()
        await cleanup()
        await on_shutdown(None, bot)

    dispatcher.startup.register(on_startup_wrapper)
    dispatcher.shutdown.register(on_shutdown_wrapper)

    # Setup graceful shutdown (Unix only)
    import platform

    if platform.system() != "Windows":
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
        await dispatcher.start_polling(_bot)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        raise
    finally:
        await cleanup()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
