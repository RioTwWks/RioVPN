"""YooKassa payment service implementation."""

import base64
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

import aiohttp
from aiohttp import BasicAuth

from src.core.config import settings
from src.core.database import AsyncSession
from src.models.payment import PaymentProvider, PaymentStatus
from src.services.payment.base import (
    PaymentData,
    PaymentGateway,
    PaymentResult,
    PaymentService,
)

logger = logging.getLogger(__name__)


@dataclass
class YooKassaConfig:
    """YooKassa API configuration."""

    shop_id: str
    secret_key: str
    base_url: str = "https://api.yookassa.ru/v3"


class YooKassaService(PaymentService):
    """
    YooKassa payment service.

    Supports RUB payments via bank cards, Sberbank, etc.
    Documentation: https://yookassa.ru/developers/api
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize YooKassa service.

        Args:
            session: Database session
        """
        super().__init__(session)
        self.config = YooKassaConfig(
            shop_id=settings.yookassa_shop_id or "",
            secret_key=settings.yookassa_secret_key or "",
            base_url="https://api.yookassa.ru/v3",
        )
        self._auth = BasicAuth(
            login=self.config.shop_id,
            password=self.config.secret_key,
        )

    @property
    def gateway(self) -> PaymentGateway:
        """Get payment gateway identifier."""
        return PaymentGateway.YOOKASSA

    def _generate_idempotence_key(self) -> str:
        """
        Generate unique idempotence key.

        Returns:
            Unique key for request deduplication
        """
        timestamp = datetime.utcnow().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:36]

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        idempotence_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Make API request to YooKassa.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            idempotence_key: Key for idempotent requests

        Returns:
            API response

        Raises:
            Exception: If request fails
        """
        url = f"{self.config.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Idempotence-Key": idempotence_key or self._generate_idempotence_key(),
        }

        async with aiohttp.ClientSession(
            auth=self._auth,
            headers=headers,
        ) as session:
            async with session.request(method, url, json=data) as response:
                result = await response.json()

                if response.status >= 400:
                    logger.error(f"YooKassa API error: {result}")
                    raise Exception(f"YooKassa API error: {result}")

                return result

    async def create_payment(
        self,
        payment_data: PaymentData,
    ) -> PaymentResult:
        """
        Create a new payment in YooKassa.

        Args:
            payment_data: Payment data

        Returns:
            Payment result with confirmation URL
        """
        try:
            # Create payment request
            expires_at = (datetime.utcnow() + timedelta(minutes=30)).isoformat()

            request_data = {
                "amount": {
                    "value": str(payment_data.amount),
                    "currency": payment_data.currency,
                },
                "capture": True,  # Auto-capture payment
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/riovpn_bot",
                },
                "description": payment_data.description,
                "expires_at": expires_at,
            }

            response = await self._request("POST", "/payments", request_data)

            payment_id = response.get("id")
            status = response.get("status")
            confirmation = response.get("confirmation", {})
            confirmation_url = confirmation.get("confirmation_url")

            if not payment_id:
                raise Exception("Invalid payment response")

            # Create payment record in database
            await self.create_payment_record(
                payment_data=payment_data,
                external_id=payment_id,
                provider=PaymentProvider.yookassa,
            )

            logger.info(f"YooKassa payment created: {payment_id}, " f"amount={payment_data.amount}, url={confirmation_url}")

            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=confirmation_url,
                confirmation_data=confirmation,
            )

        except Exception as e:
            logger.error(f"Failed to create YooKassa payment: {e}", exc_info=True)
            return PaymentResult(
                success=False,
                error_message=str(e),
            )

    async def get_payment_status(
        self,
        payment_id: str,
    ) -> Optional[PaymentStatus]:
        """
        Get payment status from YooKassa.

        Args:
            payment_id: Payment ID

        Returns:
            Payment status or None if not found
        """
        try:
            response = await self._request("GET", f"/payments/{payment_id}")

            status = response.get("status")

            # Map YooKassa status to our PaymentStatus
            status_map = {
                "pending": PaymentStatus.pending,
                "waiting_for_capture": PaymentStatus.paid,
                "succeeded": PaymentStatus.paid,
                "canceled": PaymentStatus.failed,
                "failed": PaymentStatus.failed,
            }

            return status_map.get(status, PaymentStatus.pending)

        except Exception as e:
            logger.error(f"Failed to get payment status: {e}", exc_info=True)
            return None

    async def cancel_payment(
        self,
        payment_id: str,
    ) -> bool:
        """
        Cancel/refund payment.

        Args:
            payment_id: Payment ID

        Returns:
            True if cancelled successfully
        """
        try:
            await self._request("POST", f"/payments/{payment_id}/cancel")
            logger.info(f"Payment cancelled: {payment_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel payment: {e}")
            return False

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify YooKassa webhook signature.

        YooKassa sends a SHA256 HMAC signature.

        Args:
            payload: Raw webhook payload
            signature: Signature from headers (X-Signature)

        Returns:
            True if signature is valid
        """
        try:
            # YooKassa uses SHA256 HMAC with secret key
            expected_sign = hmac.new(
                self.config.secret_key.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature.lower(), expected_sign.lower())

        except Exception as e:
            logger.error(f"Failed to verify webhook signature: {e}")
            return False

    def parse_webhook_payload(
        self,
        payload: bytes,
    ) -> Tuple[Optional[str], Optional[PaymentStatus]]:
        """
        Parse YooKassa webhook payload.

        Args:
            payload: Raw webhook payload

        Returns:
            Tuple of (payment_id, status)
        """
        try:
            data = json.loads(payload.decode())

            # YooKassa webhook structure
            event_type = data.get("event")  # payment.succeeded, payment.canceled, etc.
            payment_object = data.get("object", {})
            payment_id = payment_object.get("id")
            status = payment_object.get("status")

            # Map event type and status to PaymentStatus
            if event_type == "payment.succeeded":
                payment_status = PaymentStatus.paid
            elif event_type == "payment.canceled":
                payment_status = PaymentStatus.failed
            elif event_type == "payment.waiting_for_capture":
                payment_status = PaymentStatus.paid
            else:
                # Map by status
                status_map = {
                    "pending": PaymentStatus.pending,
                    "waiting_for_capture": PaymentStatus.paid,
                    "succeeded": PaymentStatus.paid,
                    "canceled": PaymentStatus.failed,
                    "failed": PaymentStatus.failed,
                }
                payment_status = status_map.get(status, PaymentStatus.pending)

            logger.info(
                f"Webhook received: event={event_type}, payment_id={payment_id}, " f"status={status}, mapped={payment_status}"
            )

            return payment_id, payment_status

        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}", exc_info=True)
            return None, None

    async def get_payment_info(
        self,
        payment_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed payment information.

        Args:
            payment_id: Payment ID

        Returns:
            Payment information or None
        """
        try:
            return await self._request("GET", f"/payments/{payment_id}")
        except Exception as e:
            logger.error(f"Failed to get payment info: {e}")
            return None

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
    ) -> bool:
        """
        Create refund for payment.

        Args:
            payment_id: Payment ID
            amount: Refund amount (None = full refund)

        Returns:
            True if refund created successfully
        """
        try:
            request_data = {
                "amount": {
                    "value": str(amount) if amount else "full",
                    "currency": "RUB",
                }
            }

            await self._request("POST", f"/payments/{payment_id}/refund", request_data)
            logger.info(f"Refund created for payment: {payment_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create refund: {e}")
            return False
