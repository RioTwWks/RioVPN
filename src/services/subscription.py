"""Subscription service for managing VPN subscriptions."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select

from src.core.config import settings
from src.core.database import AsyncSession
from src.models.payment import PaymentStatus
from src.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionType,
)
from src.models.user import User
from src.services.hiddify import HiddifyService
from src.services.three_xui import ThreeXuiService

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service for managing VPN subscriptions.

    Handles creation, renewal, and management of subscriptions
    across both 3x-ui (RU) and Hiddify (EU) panels.
    """

    def __init__(
        self,
        session: AsyncSession,
        three_xui: Optional[ThreeXuiService] = None,
        hiddify: Optional[HiddifyService] = None,
    ):
        """
        Initialize subscription service.

        Args:
            session: Database session
            three_xui: 3x-ui service instance
            hiddify: Hiddify service instance
        """
        self.session = session
        self.three_xui = three_xui or ThreeXuiService()
        self.hiddify = hiddify or HiddifyService()

    async def create_subscription(
        self,
        user: User,
        sub_type: SubscriptionType,
        duration_days: int = 30,
    ) -> Subscription:
        """
        Create new subscription for user.

        Args:
            user: User model instance
            sub_type: Subscription type (RU or EU)
            duration_days: Subscription duration in days

        Returns:
            Created subscription with access link

        Raises:
            Exception: If panel API call fails
        """
        now = datetime.utcnow()
        expiry = now + timedelta(days=duration_days)

        # Determine traffic limit based on type
        traffic_limit = (
            settings.default_traffic_limit_ru
            if sub_type == SubscriptionType.ru
            else settings.default_traffic_limit_eu
        )

        # Create subscription record (pending)
        subscription = Subscription(
            user_id=user.id,
            type=sub_type,
            status=SubscriptionStatus.active,
            start_date=now,
            expiry_date=expiry,
            traffic_limit=traffic_limit,
            traffic_used=0,
        )

        try:
            if sub_type == SubscriptionType.ru:
                # Create client in 3x-ui
                await self._create_ru_client(user, subscription)
            else:
                # Create user in Hiddify
                await self._create_eu_user(user, subscription)

            self.session.add(subscription)
            await self.session.commit()
            await self.session.refresh(subscription)

            logger.info(
                f"Subscription created for user {user.telegram_id}: "
                f"type={sub_type.value}, expiry={expiry}"
            )

            return subscription

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create subscription: {e}", exc_info=True)
            raise

    async def _create_ru_client(
        self, user: User, subscription: Subscription
    ) -> None:
        """
        Create client in 3x-ui panel.

        Args:
            user: User model instance
            subscription: Subscription model instance
        """
        # Generate unique email and UUID
        email = f"user_{user.telegram_id}_{uuid.uuid4().hex[:8]}"
        client_uuid = str(uuid.uuid4())

        # Get inbound ID
        inbound = await self.three_xui.get_inbound_by_tag(settings.inbound_ru_tag)
        if not inbound:
            raise Exception(f"Inbound {settings.inbound_ru_tag} not found")

        inbound_id = inbound.get("id")

        # Calculate expiry time in milliseconds
        expiry_ms = int(subscription.expiry_date.timestamp() * 1000)

        # Add client to 3x-ui
        await self.three_xui.add_client(
            inbound_id=inbound_id,
            email=email,
            uuid=client_uuid,
            traffic_limit=subscription.traffic_limit,
            expiry_time=expiry_ms,
        )

        # Generate vless:// link
        link = self._generate_ru_link(
            uuid=client_uuid,
            email=email,
        )

        subscription.panel_uuid = email  # Use email as identifier for 3x-ui
        subscription.inbound_tag = settings.inbound_ru_tag
        subscription.link = link

    def _generate_ru_link(self, uuid: str, email: str) -> str:
        """
        Generate vless:// link for Russian server.

        Args:
            uuid: Client UUID
            email: Client email (used for remark)

        Returns:
            vless:// subscription link
        """
        # Build vless URL with Reality + XHTTP parameters
        params = {
            "encryption": "none",
            "flow": "xtls-rprx-vision",
            "security": "reality",
            "sni": settings.sni_ru,
            "fp": "chrome",
            "pbk": settings.public_key_ru,
            "sid": settings.short_id_ru,
            "type": "xhttp",
            "path": "/",
            "mode": "auto",
        }

        # Build query string
        query = "&".join(f"{k}={v}" for k, v in params.items())

        # Format: vless://uuid@server:port?params#remark
        link = (
            f"vless://{uuid}@{settings.server_address_ru}:{settings.server_port_ru}"
            f"?{query}#{email}"
        )

        return link

    async def _create_eu_user(
        self, user: User, subscription: Subscription
    ) -> None:
        """
        Create user in Hiddify panel.

        Args:
            user: User model instance
            subscription: Subscription model instance
        """
        # Generate unique username
        username = f"eu_{user.telegram_id}_{uuid.uuid4().hex[:8]}"

        # Calculate expiry time in milliseconds
        expiry_ms = int(subscription.expiry_date.timestamp() * 1000)

        # Create user in Hiddify
        user_data = await self.hiddify.create_user(
            username=username,
            expiry_time=expiry_ms,
            traffic_limit=subscription.traffic_limit,
        )

        # Extract UUID and link from response
        user_uuid = user_data.get("uuid") or user_data.get("data", {}).get("uuid")
        subscription_link = user_data.get("subscription_url") or user_data.get(
            "data", {}
        ).get("subscription_url")

        if not user_uuid:
            raise Exception("Failed to get UUID from Hiddify response")

        subscription.panel_uuid = user_uuid
        subscription.link = subscription_link or f"hiddify://{user_uuid}"

    async def renew_subscription(
        self,
        subscription: Subscription,
        duration_days: int = 30,
    ) -> Subscription:
        """
        Renew existing subscription.

        Args:
            subscription: Subscription to renew
            duration_days: Renewal duration in days

        Returns:
            Updated subscription
        """
        now = datetime.utcnow()

        # Extend expiry from current date or now if expired
        if subscription.expiry_date > now:
            new_expiry = subscription.expiry_date + timedelta(days=duration_days)
        else:
            new_expiry = now + timedelta(days=duration_days)

        subscription.expiry_date = new_expiry
        subscription.status = SubscriptionStatus.active
        subscription.traffic_used = 0  # Reset traffic on renewal

        try:
            # Update in panel
            if subscription.type == SubscriptionType.ru:
                expiry_ms = int(new_expiry.timestamp() * 1000)
                await self.three_xui.update_client(
                    email=subscription.panel_uuid,
                    traffic_limit=subscription.traffic_limit,
                    expiry_time=expiry_ms,
                )
            else:
                expiry_ms = int(new_expiry.timestamp() * 1000)
                await self.hiddify.update_user(
                    uuid=subscription.panel_uuid,
                    expiry_time=expiry_ms,
                    traffic_limit=subscription.traffic_limit,
                )

            await self.session.commit()
            await self.session.refresh(subscription)

            logger.info(
                f"Subscription {subscription.id} renewed until {new_expiry}"
            )

            return subscription

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to renew subscription: {e}", exc_info=True)
            raise

    async def block_subscription(
        self,
        subscription: Subscription,
        reason: str = "expired",
    ) -> Subscription:
        """
        Block subscription and remove from panel.

        Args:
            subscription: Subscription to block
            reason: Reason for blocking

        Returns:
            Updated subscription
        """
        subscription.status = SubscriptionStatus.blocked

        try:
            # Remove from panel
            if subscription.type == SubscriptionType.ru:
                if subscription.panel_uuid:
                    await self.three_xui.delete_client(subscription.panel_uuid)
            else:
                if subscription.panel_uuid:
                    await self.hiddify.delete_user(subscription.panel_uuid)

            await self.session.commit()

            logger.info(
                f"Subscription {subscription.id} blocked: {reason}"
            )

            return subscription

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to block subscription: {e}", exc_info=True)
            raise

    async def get_user_subscription(
        self, user: User
    ) -> Optional[Subscription]:
        """
        Get active subscription for user.

        Args:
            user: User model instance

        Returns:
            Active subscription or None
        """
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .where(Subscription.status == SubscriptionStatus.active)
            .order_by(Subscription.expiry_date.desc())
        )
        return result.scalar_one_or_none()

    async def sync_traffic(self) -> int:
        """
        Sync traffic usage from panels.

        Returns:
            Number of subscriptions updated
        """
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.active
            )
        )
        subscriptions = result.scalars().all()

        updated = 0
        for sub in subscriptions:
            try:
                if sub.type == SubscriptionType.ru and sub.panel_uuid:
                    traffic = await self.three_xui.get_client_traffic(
                        sub.panel_uuid
                    )
                    sub.traffic_used = traffic.get("total", 0)
                    updated += 1
                elif sub.type == SubscriptionType.eu and sub.panel_uuid:
                    traffic = await self.hiddify.get_user_traffic(
                        sub.panel_uuid
                    )
                    sub.traffic_used = traffic.get("used", 0)
                    updated += 1
            except Exception as e:
                logger.warning(
                    f"Failed to sync traffic for subscription {sub.id}: {e}"
                )

        await self.session.commit()
        return updated
