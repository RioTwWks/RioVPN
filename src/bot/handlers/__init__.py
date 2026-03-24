"""Bot handlers module."""

from src.bot.handlers.admin import admin_router
from src.bot.handlers.callback import callback_router
from src.bot.handlers.command import command_router

__all__ = ["command_router", "callback_router", "admin_router"]
