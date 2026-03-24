"""Base payment service and webhook handler interfaces."""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select

from src.core.database import AsyncSession
from src.models.payment import Payment, PaymentProvider, PaymentStatus
from src.models.subscription import Subscription, SubscriptionType
from src.models.user import User
from src.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)


class PaymentGateway(Enum):
    """Supported payment gateways."""

    CRYPTOMUS = "cryptomus"
    YOOKASSA = "yookassa"
    TELEGRAM_STARS = "telegram_stars"


@dataclass
class PaymentData:
    """Payment data for creating a payment."""

    amount: Decimal
    currency: str
    user_id: int
    subscription_type: SubscriptionType
    duration_months: int
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "amount": str(self.amount),
            "currency": self.currency,
            "user_id": self.user_id,
            "subscription_type": self.subscription_type.value,
            "duration_months": self.duration_months,
            "description": self.description,
        }


@dataclass
class PaymentResult:
    """Result of payment creation."""

    success: bool
    payment_id: Optional[str] = None
    payment_url: Optional[str] = None
    confirmation_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class PaymentService(ABC):
    """
    Abstract base class for payment services.

    All payment providers must implement this interface.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize payment service.

        Args:
            session: Database session
        """
        self.session = session

    @property
    @abstractmethod
    def gateway(self) -> PaymentGateway:
        """Get payment gateway identifier."""
        pass

    @abstractmethod
    async def create_payment(
        self,
        payment_data: PaymentData,
    ) -> PaymentResult:
        """
        Create a new payment.

        Args:
            payment_data: Payment data

        Returns:
            Payment result with payment URL or confirmation data
        """
        pass

    @abstractmethod
    async def get_payment_status(
        self,
        payment_id: str,
    ) -> Optional[PaymentStatus]:
        """
        Get payment status from gateway.

        Args:
            payment_id: Payment ID

        Returns:
            Payment status or None if not found
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Signature from headers

        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    def parse_webhook_payload(
        self,
        payload: bytes,
    ) -> Tuple[Optional[str], Optional[PaymentStatus]]:
        """
        Parse webhook payload.

        Args:
            payload: Raw webhook payload

        Returns:
            Tuple of (payment_id, status)
        """
        pass

    async def create_payment_record(
        self,
        payment_data: PaymentData,
        external_id: str,
        provider: PaymentProvider,
    ) -> Payment:
        """
        Create payment record in database.

        Args:
            payment_data: Payment data
            external_id: External payment ID
            provider: Payment provider

        Returns:
            Created Payment record
        """
        payment = Payment(
            user_id=payment_data.user_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            status=PaymentStatus.pending,
            provider=provider,
            external_id=external_id,
            description=payment_data.description,
        )
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        logger.info(f"Payment record created: {payment.id}, external_id={external_id}")
        return payment

    async def update_payment_status(
        self,
        external_id: str,
        status: PaymentStatus,
    ) -> Optional[Payment]:
        """
        Update payment status in database.

        Args:
            external_id: External payment ID
            status: New payment status

        Returns:
            Updated Payment record
        """
        result = await self.session.execute(
            select(Payment).where(Payment.external_id == external_id)
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = status
            await self.session.commit()
            await self.session.refresh(payment)
            logger.info(f"Payment {payment.id} status updated to {status.value}")
            return payment

        logger.warning(f"Payment not found: external_id={external_id}")
        return None

    async def activate_subscription(
        self,
        payment: Payment,
    ) -> Optional[Subscription]:
        """
        Activate subscription after successful payment.

        Args:
            payment: Payment record

        Returns:
            Created subscription or None
        """
        if payment.status != PaymentStatus.paid:
            logger.warning(f"Cannot activate subscription: payment {payment.id} not paid")
            return None

        # Parse subscription data from description
        # Format: "Subscription: {type}_{duration}"
        try:
            parts = payment.description.split(": ")
            if len(parts) < 2:
                raise ValueError("Invalid description format")

            sub_parts = parts[1].split("_")
            sub_type = SubscriptionType(sub_parts[0])
            duration = int(sub_parts[1])

            # Get user
            result = await self.session.execute(
                select(User).where(User.id == payment.user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User not found: {payment.user_id}")
                return None

            # Create subscription
            service = SubscriptionService(self.session)
            subscription = await service.create_subscription(
                user=user,
                sub_type=sub_type,
                duration_days=duration * 30,
            )

            logger.info(
                f"Subscription activated for payment {payment.id}: "
                f"subscription_id={subscription.id}"
            )

            return subscription

        except Exception as e:
            logger.error(f"Failed to activate subscription: {e}", exc_info=True)
            return None

    async def process_payment_update(
        self,
        external_id: str,
        status: PaymentStatus,
    ) -> Tuple[bool, str]:
        """
        Process payment status update from webhook.

        Args:
            external_id: External payment ID
            status: New payment status

        Returns:
            Tuple of (success, message)
        """
        # Update payment status
        payment = await self.update_payment_status(
            external_id=external_id,
            status=status,
        )

        if not payment:
            return False, f"Payment not found: {external_id}"

        # Activate subscription if payment is successful
        if status == PaymentStatus.paid:
            subscription = await self.activate_subscription(payment)
            if subscription:
                return True, f"Subscription activated: {subscription.id}"
            return False, "Failed to activate subscription"

        return True, f"Payment status updated to {status.value}"


class PaymentWebhookHandler(ABC):
    """
    Abstract base class for payment webhook handlers.

    Handles incoming webhooks from payment providers.
    """

    def __init__(self, session: AsyncSession, payment_service: PaymentService):
        """
        Initialize webhook handler.

        Args:
            session: Database session
            payment_service: Payment service instance
        """
        self.session = session
        self.payment_service = payment_service

    @abstractmethod
    async def handle_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> Tuple[bool, str]:
        """
        Handle incoming webhook.

        Args:
            payload: Raw webhook payload
            signature: Signature from headers

        Returns:
            Tuple of (success, message)
        """
        pass
