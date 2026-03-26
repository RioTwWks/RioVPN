"""Bot configuration and router setup."""

import logging
from typing import Literal, Optional, Tuple, Union

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiohttp import BasicAuth

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

ProxyMode = Literal["direct", "socks5", "http", "ssh_tunnel"]
ProxyConfig = Union[Tuple[str, Optional[BasicAuth]], None]


def _build_proxy_url_with_auth(proxy_url: str, login: Optional[str], password: Optional[str]) -> str:
    """
    Build proxy URL with authentication if credentials are provided.

    Args:
        proxy_url: Base proxy URL (e.g., socks5://127.0.0.1:10808)
        login: Optional authentication login
        password: Optional authentication password

    Returns:
        Proxy URL with embedded credentials if provided
    """
    if not login or not password:
        return proxy_url

    # Parse proxy URL to insert credentials
    # Format: protocol://host:port -> protocol://login:password@host:port
    try:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(proxy_url)
        if parsed.hostname:
            # Rebuild URL with credentials
            netloc = f"{login}:{password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            elif parsed.username:  # Already has credentials
                return proxy_url
            return urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        # Fallback: simple string replacement
        pass

    return proxy_url


def _get_proxy_config() -> ProxyConfig:
    """
    Build proxy configuration for AiohttpSession based on PROXY_MODE.

    Supported modes:
    - 'direct': No proxy (returns None)
    - 'socks5': SOCKS5 proxy (e.g., local 3x-ui inbound or v2ray client)
    - 'http': HTTP proxy
    - 'ssh_tunnel': SSH tunnel mode (uses SOCKS5 settings, for documentation)

    Returns:
        Tuple of (proxy_url, auth) or None if direct connection
    """
    mode = settings.proxy_mode

    # Direct connection - no proxy
    if mode == "direct":
        logger.info("Using direct connection (no proxy)")
        return None

    # SSH tunnel mode uses the same settings as SOCKS5
    # (the tunnel is established externally via SSH)
    effective_mode = "socks5" if mode == "ssh_tunnel" else mode

    if not settings.proxy_url:
        logger.warning(f"Proxy mode is '{mode}' but PROXY_URL is not set. Using direct connection.")
        return None

    # Build proxy URL with authentication
    proxy_url = _build_proxy_url_with_auth(
        settings.proxy_url,
        settings.proxy_login,
        settings.proxy_password,
    )

    logger.info(f"Using proxy mode: {mode} (effective: {effective_mode}) via {proxy_url}")

    # For aiogram, we pass the URL directly or as tuple with BasicAuth
    auth: Optional[BasicAuth] = None
    if settings.proxy_login and settings.proxy_password:
        auth = BasicAuth(login=settings.proxy_login, password=settings.proxy_password)

    return (proxy_url, auth)


def create_bot() -> Bot:
    """
    Create bot instance with default properties and proxy configuration.

    Returns:
        Configured Bot instance
    """
    # Setup session with proxy if configured
    proxy_config = _get_proxy_config()

    if proxy_config:
        session = AiohttpSession(proxy=proxy_config)
        # Disable SSL verification for proxy connections to handle
        # self-signed certificates and proxy SSL inspection
        session._connector_init["ssl"] = False
    else:
        session = AiohttpSession()

    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
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
        admin_manage_router,
        admin_router,
        broadcast_router,
        callback_router,
        command_router,
        payment_history_router,
        payment_router,
        referral_router,
        renewal_router,
        test_router,
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
    root_router.include_router(admin_manage_router)
    root_router.include_router(test_router)

    return root_router
