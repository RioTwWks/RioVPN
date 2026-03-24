"""Notification service for sending messages to users."""

import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select

from src.core.logging import get_logger
from src.models.subscription import Subscription
from src.models.user import User

logger = get_logger(__name__)


class NotificationService:
    """
    Service for sending notifications to users.

    Handles all user-facing messages including:
    - Expiry reminders
    - Traffic warnings
    - Payment confirmations
    - System announcements
    """

    def __init__(self, bot: Bot):
        """
        Initialize notification service.

        Args:
            bot: Bot instance
        """
        self.bot = bot

    async def send_message(
        self,
        telegram_id: int,
        text: str,
        parse_mode: str = "HTML",
    ) -> bool:
        """
        Send message to user.

        Args:
            telegram_id: User's Telegram ID
            text: Message text
            parse_mode: Parse mode (HTML, Markdown)

        Returns:
            True if message sent successfully
        """
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode=parse_mode,
            )
            logger.debug(f"Message sent to user {telegram_id}")
            return True

        except TelegramForbiddenError:
            logger.warning(f"User {telegram_id} blocked the bot")
            return False

        except TelegramBadRequest as e:
            logger.warning(f"Failed to send message to {telegram_id}: {e}")
            return False

        except Exception as e:
            logger.error(f"Error sending message to {telegram_id}: {e}", exc_info=True)
            return False

    async def send_expiry_reminder(
        self,
        user: User,
        subscription: Subscription,
    ) -> bool:
        """
        Send subscription expiry reminder.

        Args:
            user: User instance
            subscription: Subscription instance

        Returns:
            True if message sent successfully
        """
        if not user.telegram_id:
            return False

        days = subscription.days_remaining
        type_emoji = "🇷🇺" if subscription.type.value == "ru" else "🇪🇺"

        text = (
            f"⏰ <b>Напоминание об окончании подписки</b>\n\n"
            f"{type_emoji} <b>Тип:</b> {subscription.type.value.upper()}\n"
            f"📅 <b>Истекает через:</b> {days} дн.\n"
            f"📅 <b>Дата окончания:</b> {subscription.expiry_date.strftime('%d.%m.%Y')}\n\n"
            f"Продлите подписку заранее, чтобы не потерять доступ к VPN!\n\n"
            f"Для продления используйте команду /renew"
        )

        return await self.send_message(user.telegram_id, text)

    async def send_traffic_warning(
        self,
        user: User,
        subscription: Subscription,
        percent_used: float,
    ) -> bool:
        """
        Send traffic limit warning.

        Args:
            user: User instance
            subscription: Subscription instance
            percent_used: Percentage of traffic used

        Returns:
            True if message sent successfully
        """
        if not user.telegram_id:
            return False

        used_gb = subscription.traffic_used / (1024**3)
        limit_gb = subscription.traffic_limit / (1024**3) if subscription.traffic_limit else 0

        text = (
            f"⚠️ <b>Предупреждение о трафике</b>\n\n"
            f"📊 <b>Использовано:</b> {percent_used:.1f}%\n"
            f"💾 <b>Трафик:</b> {used_gb:.2f} ГБ из {limit_gb:.2f} ГБ\n\n"
            f"Ваш трафик подходит к концу. При превышении лимита подписка будет заблокирована.\n\n"
            f"Для продления используйте команду /renew"
        )

        return await self.send_message(user.telegram_id, text)

    async def send_payment_success(
        self,
        user: User,
        subscription: Subscription,
    ) -> bool:
        """
        Send payment success notification.

        Args:
            user: User instance
            subscription: Subscription instance

        Returns:
            True if message sent successfully
        """
        if not user.telegram_id:
            return False

        type_emoji = "🇷🇺" if subscription.type.value == "ru" else "🇪🇺"

        text = (
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"{type_emoji} <b>Тип:</b> {subscription.type.value.upper()}\n"
            f"📅 <b>Действует до:</b> {subscription.expiry_date.strftime('%d.%m.%Y')}\n"
            f"⏳ <b>Осталось дней:</b> {subscription.days_remaining}\n\n"
            f"🔗 <b>Ваша ссылка для подключения:</b>\n"
            f"<code>{subscription.link}</code>\n\n"
            f"Также вы можете найти ссылку в разделе /my"
        )

        return await self.send_message(user.telegram_id, text)

    async def send_subscription_blocked(
        self,
        user: User,
        subscription: Subscription,
        reason: str,
    ) -> bool:
        """
        Send subscription blocked notification.

        Args:
            user: User instance
            subscription: Subscription instance
            reason: Reason for blocking

        Returns:
            True if message sent successfully
        """
        if not user.telegram_id:
            return False

        reason_text = "истек срок действия" if reason == "expired" else "превышен лимит трафика"

        text = (
            f"❌ <b>Подписка заблокирована</b>\n\n"
            f"Причина: {reason_text}\n\n"
            f"Для возобновления доступа продлите подписку через /renew"
        )

        return await self.send_message(user.telegram_id, text)


# Global bot instance for notifications
_notification_bot: Optional[Bot] = None
_notification_service: Optional[NotificationService] = None


def init_notifications(bot: Bot) -> NotificationService:
    """
    Initialize notification service with bot instance.

    Args:
        bot: Bot instance

    Returns:
        NotificationService instance
    """
    global _notification_bot, _notification_service
    _notification_bot = bot
    _notification_service = NotificationService(bot)
    return _notification_service


def get_notification_service() -> Optional[NotificationService]:
    """
    Get notification service instance.

    Returns:
        NotificationService instance or None
    """
    return _notification_service
