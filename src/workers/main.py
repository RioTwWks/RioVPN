"""Worker entry point for background tasks."""

import asyncio
import logging
import signal

from src.core.logging import setup_logging
from src.workers.scheduler import run_scheduler

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main worker runner."""
    # Setup logging
    setup_logging("INFO")

    logger.info("Worker starting...")

    # Setup signal handlers
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_signal():
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    try:
        # Run scheduler
        await run_scheduler()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
