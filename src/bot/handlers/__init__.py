"""Bot handlers module."""

from src.bot.handlers.admin import admin_router
from src.bot.handlers.broadcast import broadcast_router
from src.bot.handlers.callback import callback_router
from src.bot.handlers.command import command_router
from src.bot.handlers.payment import payment_router
from src.bot.handlers.payments import payment_history_router
from src.bot.handlers.referral import referral_router
from src.bot.handlers.renewal import renewal_router
from src.bot.handlers.tiers import tier_router
from src.bot.handlers.users import user_router

__all__ = [
    "command_router",
    "callback_router",
    "admin_router",
    "payment_router",
    "renewal_router",
    "broadcast_router",
    "user_router",
    "payment_history_router",
    "referral_router",
    "tier_router",
]
