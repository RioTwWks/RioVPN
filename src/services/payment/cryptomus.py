"""Cryptomus payment service implementation."""

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

import aiohttp

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
class CryptomusConfig:
    """Cryptomus API configuration."""

    api_key: str
    merchant_id: str
    base_url: str = "https://api.cryptomus.com"


class CryptomusService(PaymentService):
    """
    Cryptomus payment service.

    Supports cryptocurrency payments (USDT, BTC, ETH, etc.)
    Documentation: https://docs.cryptomus.com/
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize Cryptomus service.

        Args:
            session: Database session
        """
        super().__init__(session)
        self.config = CryptomusConfig(
            api_key=settings.cryptomus_api_key or "",
            merchant_id="",  # Not required for basic API
            base_url="https://api.cryptomus.com",
        )
        self._headers = {
            "Content-Type": "application/json",
            "merchant": self.config.merchant_id,
            "sign": self._generate_sign(""),
        }

    @property
    def gateway(self) -> PaymentGateway:
        """Get payment gateway identifier."""
        return PaymentGateway.CRYPTOMUS

    def _generate_sign(self, data: str) -> str:
        """
        Generate HMAC signature for request.

        Args:
            data: Request data as JSON string

        Returns:
            SHA256 HMAC signature
        """
        message = hashlib.sha256(hashlib.sha256(data.encode()).hexdigest().encode() + self.config.api_key.encode()).hexdigest()
        return message

    def _generate_sign_v2(self, data: Dict[str, Any], path: str) -> str:
        """
        Generate signature for API v2.

        Args:
            data: Request data
            path: API endpoint path

        Returns:
            Base64 encoded HMAC signature
        """
        json_data = json.dumps(data, separators=(",", ":"))
        b64_data = hashlib.base64.b64encode(json_data.encode()).decode()
        sign_string = b64_data + self.config.api_key
        return hashlib.sha3_256(sign_string.encode()).hexdigest()

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make API request to Cryptomus.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data

        Returns:
            API response

        Raises:
            Exception: If request fails
        """
        url = f"{self.config.base_url}{endpoint}"
        data = data or {}

        # Generate signature
        sign = self._generate_sign_v2(data, endpoint)
        headers = {
            "Content-Type": "application/json",
            "Sign": sign,
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(method, url, json=data) as response:
                result = await response.json()

                if response.status != 200:
                    logger.error(f"Cryptomus API error: {result}")
                    raise Exception(f"Cryptomus API error: {result}")

                return result

    async def create_payment(
        self,
        payment_data: PaymentData,
    ) -> PaymentResult:
        """
        Create a new payment in Cryptomus.

        Args:
            payment_data: Payment data

        Returns:
            Payment result with payment URL
        """
        try:
            # Create payment request
            request_data = {
                "amount": str(payment_data.amount),
                "currency": payment_data.currency,
                "order_id": f"vpn_{payment_data.user_id}_{int(datetime.utcnow().timestamp())}",
                "description": payment_data.description,
                "url_return": "https://t.me/riovpn_bot",  # Return to bot
                "url_success": "https://t.me/riovpn_bot",  # Success page
            }

            response = await self._request("POST", "/v1/payment", request_data)

            if response.get("state") != 1:
                raise Exception(f"Failed to create payment: {response}")

            payment_info = response.get("result", {})
            external_id = payment_info.get("order_id")
            payment_url = payment_info.get("url")

            if not external_id or not payment_url:
                raise Exception("Invalid payment response")

            # Create payment record in database
            await self.create_payment_record(
                payment_data=payment_data,
                external_id=external_id,
                provider=PaymentProvider.cryptomus,
            )

            logger.info(f"Cryptomus payment created: {external_id}, " f"amount={payment_data.amount}, url={payment_url}")

            return PaymentResult(
                success=True,
                payment_id=external_id,
                payment_url=payment_url,
                confirmation_data={"url": payment_url},
            )

        except Exception as e:
            logger.error(f"Failed to create Cryptomus payment: {e}", exc_info=True)
            return PaymentResult(
                success=False,
                error_message=str(e),
            )

    async def get_payment_status(
        self,
        payment_id: str,
    ) -> Optional[PaymentStatus]:
        """
        Get payment status from Cryptomus.

        Args:
            payment_id: Order ID

        Returns:
            Payment status or None if not found
        """
        try:
            request_data = {
                "order_id": payment_id,
            }

            response = await self._request("POST", "/v1/payment/info", request_data)

            if response.get("state") != 1:
                logger.warning(f"Failed to get payment status: {payment_id}")
                return None

            payment_info = response.get("result", {})
            status = payment_info.get("status")

            # Map Cryptomus status to our PaymentStatus
            status_map = {
                "wait": PaymentStatus.pending,
                "pay": PaymentStatus.pending,
                "paid": PaymentStatus.paid,
                "cancel": PaymentStatus.failed,
                "fail": PaymentStatus.failed,
            }

            return status_map.get(status, PaymentStatus.pending)

        except Exception as e:
            logger.error(f"Failed to get payment status: {e}", exc_info=True)
            return None

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify Cryptomus webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Signature from headers

        Returns:
            True if signature is valid
        """
        try:
            # Cryptomus sends MD5 hash of the request body + API key
            expected_sign = hashlib.md5(payload + self.config.api_key.encode()).hexdigest()

            return hmac.compare_digest(signature.lower(), expected_sign.lower())

        except Exception as e:
            logger.error(f"Failed to verify webhook signature: {e}")
            return False

    def parse_webhook_payload(
        self,
        payload: bytes,
    ) -> Tuple[Optional[str], Optional[PaymentStatus]]:
        """
        Parse Cryptomus webhook payload.

        Args:
            payload: Raw webhook payload

        Returns:
            Tuple of (order_id, status)
        """
        try:
            data = json.loads(payload.decode())

            order_id = data.get("order_id")
            status = data.get("status")

            # Map status
            status_map = {
                "wait": PaymentStatus.pending,
                "pay": PaymentStatus.pending,
                "paid": PaymentStatus.paid,
                "cancel": PaymentStatus.failed,
                "fail": PaymentStatus.failed,
            }

            payment_status = status_map.get(status)

            logger.info(f"Webhook received: order_id={order_id}, status={status}, " f"mapped={payment_status}")

            return order_id, payment_status

        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}", exc_info=True)
            return None, None

    async def get_currencies(self) -> Dict[str, Any]:
        """
        Get available payment currencies.

        Returns:
            Dictionary of available currencies
        """
        try:
            response = await self._request("POST", "/v1/currency/list", {})
            return response.get("result", {})
        except Exception as e:
            logger.error(f"Failed to get currencies: {e}")
            return {}
