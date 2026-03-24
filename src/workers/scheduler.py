"""Background scheduler configuration and runner."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.core.database import get_session
from src.core.logging import get_logger
from src.workers.jobs import (
    check_expiring_subscriptions,
    check_traffic_warnings,
    send_reminders,
    set_bot,
    sync_traffic,
)

logger = get_logger(__name__)


class Scheduler:
    """
    Background job scheduler for subscription management.

    Handles periodic tasks like:
    - Checking expiring subscriptions
    - Syncing traffic from panels
    - Sending expiry reminders
    - Auto-blocking expired subscriptions
    """

    def __init__(self, bot: Optional[Bot] = None):
        """
        Initialize scheduler.

        Args:
            bot: Bot instance for notifications
        """
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
        self.bot = bot

    def start(self) -> None:
        """
        Start the scheduler.

        Registers all periodic jobs and starts the scheduler.
        """
        if self.scheduler and self.scheduler.running:
            logger.warning("Scheduler already running")
            return

        # Set bot for jobs
        if self.bot:
            set_bot(self.bot)

        self.scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 60,
            },
        )

        # Register jobs
        self._register_jobs()

        self.scheduler.start()
        self._running = True

        logger.info(
            "Scheduler started with jobs:\n"
            "  - check_expiring_subscriptions (every hour)\n"
            "  - sync_traffic (daily at 03:00 UTC)\n"
            "  - send_reminders (daily at 09:00 UTC)\n"
            "  - check_traffic_warnings (every 6 hours)"
        )

    def stop(self) -> None:
        """
        Stop the scheduler.

        Gracefully shuts down all running jobs.
        """
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Scheduler stopped")

    def _register_jobs(self) -> None:
        """Register all periodic jobs with the scheduler."""
        if not self.scheduler:
            return

        # Check expiring subscriptions every hour
        self.scheduler.add_job(
            self._run_job,
            IntervalTrigger(hours=1),
            id="check_expiring_subscriptions",
            name="Check expiring subscriptions",
            args=(check_expiring_subscriptions,),
            replace_existing=True,
        )

        # Sync traffic daily at 03:00 UTC
        self.scheduler.add_job(
            self._run_job,
            CronTrigger(hour=3, minute=0),
            id="sync_traffic",
            name="Sync traffic from panels",
            args=(sync_traffic,),
            replace_existing=True,
        )

        # Send expiry reminders daily at 09:00 UTC
        self.scheduler.add_job(
            self._run_job,
            CronTrigger(hour=9, minute=0),
            id="send_reminders",
            name="Send expiry reminders",
            args=(send_reminders,),
            replace_existing=True,
        )

        # Check traffic warnings every 6 hours
        self.scheduler.add_job(
            self._run_job,
            IntervalTrigger(hours=6),
            id="check_traffic_warnings",
            name="Check traffic warnings",
            args=(check_traffic_warnings,),
            replace_existing=True,
        )

    async def _run_job(self, job_func) -> None:
        """
        Run a job with proper session management.

        Args:
            job_func: Async function to execute
        """
        job_name = job_func.__name__
        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting job: {job_name}")
            await job_func()
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Job completed: {job_name} (duration: {duration:.2f}s)")

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                f"Job failed: {job_name} (duration: {duration:.2f}s, error: {e})",
                exc_info=True,
            )

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running


def create_scheduler(bot: Optional[Bot] = None) -> Scheduler:
    """
    Create scheduler instance.

    Args:
        bot: Bot instance for notifications

    Returns:
        Configured Scheduler instance
    """
    return Scheduler(bot=bot)


async def run_scheduler(bot: Optional[Bot] = None) -> None:
    """
    Run scheduler in background.

    This function runs until interrupted.

    Args:
        bot: Bot instance for notifications
    """
    scheduler = create_scheduler(bot=bot)
    scheduler.start()

    try:
        # Keep running
        while scheduler.is_running:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Scheduler interrupt received")
    finally:
        scheduler.stop()


if __name__ == "__main__":
    # Run scheduler directly for testing
    asyncio.run(run_scheduler())
