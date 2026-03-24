"""Bot configuration and router setup."""

import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def create_bot() -> Bot:
    """
    Create bot instance with default properties.

    Returns:
        Configured Bot instance
    """
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """
    Create dispatcher instance.

    Returns:
        Configured Dispatcher instance
    """
    return Dispatcher()


async def on_startup(dispatcher: Dispatcher, bot: Bot) -> None:
    """
    Handle bot startup.

    Args:
        dispatcher: Dispatcher instance
        bot: Bot instance
    """
    logger.info("Bot started")
    await bot.delete_webhook(drop_pending_updates=True)


async def on_shutdown(dispatcher: Dispatcher, bot: Bot) -> None:
    """
    Handle bot shutdown.

    Args:
        dispatcher: Dispatcher instance
        bot: Bot instance
    """
    logger.info("Bot stopping")
    await bot.session.close()


def setup_routers() -> Router:
    """
    Setup and register all routers.

    Returns:
        Root router with all handlers
    """
    from src.bot.handlers import (
        admin_router,
        broadcast_router,
        callback_router,
        command_router,
        payment_history_router,
        payment_router,
        referral_router,
        renewal_router,
        tier_router,
        user_router,
    )

    root_router = Router()
    root_router.include_router(command_router)
    root_router.include_router(callback_router)
    root_router.include_router(payment_router)
    root_router.include_router(renewal_router)
    root_router.include_router(broadcast_router)
    root_router.include_router(user_router)
    root_router.include_router(payment_history_router)
    root_router.include_router(referral_router)
    root_router.include_router(tier_router)
    root_router.include_router(admin_router)

    return root_router
