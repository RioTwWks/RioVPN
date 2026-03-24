"""Payment webhook handlers for the bot."""

import logging
from typing import Tuple

from aiogram import Router
from aiogram.types import HTTPException
from aiohttp import web

from src.core.database import get_session
from src.services.payment.cryptomus import CryptomusService
from src.services.payment.yookassa import YooKassaService

logger = logging.getLogger(__name__)

webhook_router = Router()


@webhook_router.post("/webhook/cryptomus")
async def handle_cryptomus_webhook(request: web.Request) -> web.Response:
    """
    Handle Cryptomus payment webhook.

    Args:
        request: Web request

    Returns:
        Web response
    """
    try:
        # Get payload and signature
        payload = await request.read()
        signature = request.headers.get("Sign", "")

        logger.info(f"Cryptomus webhook received: {payload[:100]}...")

        async for session in get_session():
            # Create service and verify signature
            service = CryptomusService(session)

            if not service.verify_webhook_signature(payload, signature):
                logger.warning("Invalid Cryptomus webhook signature")
                return web.Response(text="Invalid signature", status=403)

            # Parse payload
            order_id, status = service.parse_webhook_payload(payload)

            if not order_id or not status:
                logger.warning("Failed to parse Cryptomus webhook")
                return web.Response(text="Invalid payload", status=400)

            # Process payment update
            success, message = await service.process_payment_update(order_id, status)

            if success:
                logger.info(f"Cryptomus webhook processed: {message}")
                return web.Response(text="OK")
            else:
                logger.error(f"Cryptomus webhook failed: {message}")
                return web.Response(text=message, status=500)

    except Exception as e:
        logger.error(f"Cryptomus webhook error: {e}", exc_info=True)
        return web.Response(text="Internal error", status=500)


@webhook_router.post("/webhook/yookassa")
async def handle_yookassa_webhook(request: web.Request) -> web.Response:
    """
    Handle YooKassa payment webhook.

    Args:
        request: Web request

    Returns:
        Web response
    """
    try:
        # Get payload and signature
        payload = await request.read()
        signature = request.headers.get("X-Signature", "")
        content_type = request.headers.get("Content-Type", "")

        logger.info(f"YooKassa webhook received: {payload[:100]}...")

        async for session in get_session():
            # Create service and verify signature
            service = YooKassaService(session)

            if not service.verify_webhook_signature(payload, signature):
                logger.warning("Invalid YooKassa webhook signature")
                return web.Response(text="Invalid signature", status=403)

            # Parse payload
            payment_id, status = service.parse_webhook_payload(payload)

            if not payment_id or not status:
                logger.warning("Failed to parse YooKassa webhook")
                return web.Response(text="Invalid payload", status=400)

            # Process payment update
            success, message = await service.process_payment_update(payment_id, status)

            if success:
                logger.info(f"YooKassa webhook processed: {message}")
                return web.Response(text="OK")
            else:
                logger.error(f"YooKassa webhook failed: {message}")
                return web.Response(text=message, status=500)

    except Exception as e:
        logger.error(f"YooKassa webhook error: {e}", exc_info=True)
        return web.Response(text="Internal error", status=500)


def create_webhook_app() -> web.Application:
    """
    Create aiohttp web application for webhooks.

    Returns:
        Web application
    """
    app = web.Application()
    app.router.add_post("/webhook/cryptomus", handle_cryptomus_webhook)
    app.router.add_post("/webhook/yookassa", handle_yookassa_webhook)
    return app
