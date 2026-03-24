"""Background jobs for subscription management."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from aiogram import Bot
from sqlalchemy import select

from src.core.database import get_session
from src.core.logging import get_logger
from src.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from src.models.user import User
from src.services.hiddify import HiddifyService
from src.services.subscription import SubscriptionService
from src.services.three_xui import ThreeXuiService

logger = get_logger(__name__)

# Global bot instance for notifications
_bot: Optional[Bot] = None


def set_bot(bot: Bot) -> None:
    """Set bot instance for notifications."""
    global _bot
    _bot = bot


async def check_expiring_subscriptions() -> int:
    """
    Check and block expired subscriptions.

    Runs every hour to find and block subscriptions that have expired.

    Returns:
        Number of subscriptions blocked
    """
    async for session in get_session():
        # Find expired active subscriptions
        result = await session.execute(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.active)
            .where(Subscription.expiry_date < datetime.utcnow())
        )
        expired_subs = result.scalars().all()

        blocked_count = 0
        for sub in expired_subs:
            try:
                # Block subscription
                service = SubscriptionService(session)
                await service.block_subscription(sub, reason="expired")
                blocked_count += 1

                logger.info(f"Blocked expired subscription: {sub.id}, " f"user={sub.user_id}, expired_at={sub.expiry_date}")

            except Exception as e:
                logger.error(
                    f"Failed to block subscription {sub.id}: {e}",
                    exc_info=True,
                )

        if blocked_count > 0:
            logger.info(f"Blocked {blocked_count} expired subscriptions")

        return blocked_count

    return 0


async def sync_traffic() -> int:
    """
    Sync traffic usage from VPN panels.

    Runs daily to update traffic usage for all active subscriptions.

    Returns:
        Number of subscriptions updated
    """
    async for session in get_session():
        # Get all active subscriptions
        result = await session.execute(select(Subscription).where(Subscription.status == SubscriptionStatus.active))
        subscriptions = result.scalars().all()

        updated_count = 0
        error_count = 0

        # Initialize panel services
        three_xui = ThreeXuiService()
        hiddify = HiddifyService()

        for sub in subscriptions:
            try:
                if sub.type == SubscriptionType.ru and sub.panel_uuid:
                    # Get traffic from 3x-ui
                    traffic = await three_xui.get_client_traffic(sub.panel_uuid)
                    new_traffic = traffic.get("total", 0)

                elif sub.type == SubscriptionType.eu and sub.panel_uuid:
                    # Get traffic from Hiddify
                    traffic = await hiddify.get_user_traffic(sub.panel_uuid)
                    new_traffic = traffic.get("used", 0)

                else:
                    continue

                # Update if traffic has changed
                if new_traffic != sub.traffic_used:
                    sub.traffic_used = new_traffic
                    updated_count += 1

                    # Check if limit exceeded
                    if sub.traffic_limit and new_traffic >= sub.traffic_limit:
                        sub.status = SubscriptionStatus.blocked
                        logger.info(
                            f"Subscription {sub.id} blocked: traffic limit exceeded "
                            f"({new_traffic}/{sub.traffic_limit} bytes)"
                        )

            except Exception as e:
                error_count += 1
                logger.warning(f"Failed to sync traffic for subscription {sub.id}: {e}")

        await session.commit()

        logger.info(f"Traffic sync completed: {updated_count} updated, " f"{error_count} errors, {len(subscriptions)} total")

        return updated_count

    return 0


async def send_reminders() -> int:
    """
    Send expiry reminders to users.

    Runs daily to send reminders for subscriptions expiring soon.

    Returns:
        Number of reminders sent
    """
    if not _bot:
        logger.warning("Bot not initialized, skipping reminders")
        return 0

    from src.bot.notifications import NotificationService

    notification_service = NotificationService(_bot)

    async for session in get_session():
        # Find subscriptions expiring in 3 days
        target_date = datetime.utcnow() + timedelta(days=3)

        result = await session.execute(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.active)
            .where(
                Subscription.expiry_date >= datetime.utcnow(),
                Subscription.expiry_date <= target_date,
            )
        )
        expiring_subs = result.scalars().all()

        reminder_count = 0
        for sub in expiring_subs:
            try:
                # Get user
                user_result = await session.execute(select(User).where(User.id == sub.user_id))
                user = user_result.scalar_one_or_none()

                if user and user.telegram_id:
                    # Send reminder
                    success = await notification_service.send_expiry_reminder(
                        user=user,
                        subscription=sub,
                    )
                    if success:
                        reminder_count += 1
                        logger.info(
                            f"Reminder sent to user {user.telegram_id}: "
                            f"subscription {sub.id} expires in {sub.days_remaining} days"
                        )

            except Exception as e:
                logger.error(
                    f"Failed to send reminder for subscription {sub.id}: {e}",
                    exc_info=True,
                )

        logger.info(f"Sent {reminder_count} expiry reminders")
        return reminder_count

    return 0


async def check_traffic_warnings() -> int:
    """
    Check for users approaching traffic limits.

    Sends warnings when users reach 80% of their traffic limit.

    Returns:
        Number of warnings sent
    """
    if not _bot:
        logger.warning("Bot not initialized, skipping traffic warnings")
        return 0

    from src.bot.notifications import NotificationService

    notification_service = NotificationService(_bot)

    async for session in get_session():
        # Get active subscriptions with traffic limits
        result = await session.execute(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.active)
            .where(Subscription.traffic_limit != None)
        )
        subscriptions = result.scalars().all()

        warning_count = 0
        for sub in subscriptions:
            if sub.traffic_limit and sub.traffic_limit > 0:
                usage_percent = (sub.traffic_used / sub.traffic_limit) * 100

                # Check if in warning zone (80-100%)
                if 80 <= usage_percent < 100:
                    user_result = await session.execute(select(User).where(User.id == sub.user_id))
                    user = user_result.scalar_one_or_none()

                    if user and user.telegram_id:
                        success = await notification_service.send_traffic_warning(
                            user=user,
                            subscription=sub,
                            percent_used=usage_percent,
                        )
                        if success:
                            warning_count += 1
                            logger.info(f"Traffic warning sent to user {user.telegram_id}: " f"{usage_percent:.1f}% used")

        logger.info(f"Sent {warning_count} traffic warnings")
        return warning_count

    return 0
