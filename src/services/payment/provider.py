"""Payment provider factory and routing."""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.payment.base import PaymentService
from src.services.payment.cryptomus import CryptomusService
from src.services.payment.yookassa import YooKassaService

logger = logging.getLogger(__name__)


class PaymentProviderFactory:
    """
    Factory for creating payment service instances.

    Routes payment requests to appropriate provider based on configuration.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize factory.

        Args:
            session: Database session
        """
        self.session = session
        self._services: dict[str, PaymentService] = {}

    def get_service(self, provider: str) -> Optional[PaymentService]:
        """
        Get payment service by provider name.

        Args:
            provider: Provider name (cryptomus, yookassa)

        Returns:
            Payment service instance or None
        """
        if provider in self._services:
            return self._services[provider]

        service = self._create_service(provider)
        if service:
            self._services[provider] = service

        return service

    def _create_service(self, provider: str) -> Optional[PaymentService]:
        """
        Create payment service instance.

        Args:
            provider: Provider name

        Returns:
            Payment service instance or None
        """
        if provider == "cryptomus":
            if not settings.cryptomus_api_key:
                logger.warning("Cryptomus API key not configured")
                return None
            return CryptomusService(self.session)

        elif provider == "yookassa":
            if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
                logger.warning("YooKassa credentials not configured")
                return None
            return YooKassaService(self.session)

        else:
            logger.warning(f"Unknown payment provider: {provider}")
            return None

    def get_available_providers(self) -> list[str]:
        """
        Get list of available payment providers.

        Returns:
            List of configured provider names
        """
        available = []

        if settings.cryptomus_api_key:
            available.append("cryptomus")

        if settings.yookassa_shop_id and settings.yookassa_secret_key:
            available.append("yookassa")

        return available


def get_payment_provider(
    session: AsyncSession,
    provider: str,
) -> Optional[PaymentService]:
    """
    Get payment provider instance.

    Convenience function for getting a payment service.

    Args:
        session: Database session
        provider: Provider name

    Returns:
        Payment service instance or None
    """
    factory = PaymentProviderFactory(session)
    return factory.get_service(provider)


def get_available_payment_providers(session: AsyncSession) -> list[str]:
    """
    Get list of available payment providers.

    Args:
        session: Database session

    Returns:
        List of available provider names
    """
    factory = PaymentProviderFactory(session)
    return factory.get_available_providers()
