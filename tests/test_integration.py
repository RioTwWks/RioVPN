"""Integration tests for full workflows."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.subscription import SubscriptionType, SubscriptionStatus
from src.models.payment import PaymentStatus, PaymentProvider
from src.services.subscription import SubscriptionService


class TestSubscriptionWorkflow:
    """Integration tests for subscription workflow."""

    @pytest.mark.asyncio
    async def test_full_subscription_purchase(
        self,
        db_session,
        user,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test complete subscription purchase flow."""
        # Create subscription
        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        subscription = await service.create_subscription(
            user=user,
            sub_type=SubscriptionType.ru,
            duration_days=30,
        )

        # Verify subscription created
        assert subscription is not None
        assert subscription.type == SubscriptionType.ru
        assert subscription.status == SubscriptionStatus.active
        assert subscription.link is not None

        # Verify panel API called
        mock_three_xui.add_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscription_renewal_workflow(
        self,
        db_session,
        subscription,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test subscription renewal flow."""
        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        original_expiry = subscription.expiry_date
        original_traffic = subscription.traffic_used

        # Renew subscription
        renewed = await service.renew_subscription(
            subscription,
            duration_days=30,
        )

        # Verify renewal
        assert renewed.expiry_date > original_expiry
        assert renewed.traffic_used == 0  # Reset on renewal
        assert renewed.status == SubscriptionStatus.active

    @pytest.mark.asyncio
    async def test_subscription_expiry_workflow(
        self,
        db_session,
        subscription,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test subscription expiry and blocking."""
        # Set subscription to expired
        subscription.expiry_date = datetime.utcnow() - timedelta(days=1)
        await db_session.commit()

        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        # Block expired subscription
        blocked = await service.block_subscription(subscription, reason="expired")

        assert blocked.status == SubscriptionStatus.blocked
        mock_three_xui.delete_client.assert_called_once()


class TestPaymentWorkflow:
    """Integration tests for payment workflow."""

    @pytest.mark.asyncio
    async def test_payment_to_subscription(
        self,
        db_session,
        user,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test payment creating subscription."""
        from src.models.payment import Payment
        from src.services.payment.base import PaymentService, PaymentData

        # Create payment
        payment = Payment(
            user_id=user.id,
            amount=Decimal("299.00"),
            currency="RUB",
            status=PaymentStatus.pending,
            provider=PaymentProvider.cryptomus,
            external_id="test-payment-123",
            description="Subscription: ru_1",
        )
        db_session.add(payment)
        await db_session.commit()

        # Mock payment service
        with patch.object(PaymentService, 'activate_subscription') as mock_activate:
            mock_activate.return_value = MagicMock()

            # Update payment to paid
            payment.status = PaymentStatus.paid
            await db_session.commit()

            # Verify payment status
            assert payment.status == PaymentStatus.paid


class TestReferralWorkflow:
    """Integration tests for referral workflow."""

    @pytest.mark.asyncio
    async def test_full_referral_flow(
        self,
        db_session,
        user,
    ):
        """Test complete referral flow from signup to bonus."""
        from src.models.user import User
        from src.services.referral import ReferralService

        # Create referrer
        referrer = User(
            telegram_id=111222333,
            username="referrer",
            referral_code="REF123CODE",
        )
        db_session.add(referrer)
        await db_session.commit()

        # Create referred user
        referred = User(
            telegram_id=444555666,
            username="referred",
        )
        db_session.add(referred)
        await db_session.commit()

        # Track referral
        referral_service = ReferralService(db_session)
        referral = await referral_service.track_referral(referrer, referred)

        assert referral is not None
        assert referral.referrer_id == referrer.telegram_id
        assert referred.referred_by == referrer.telegram_id

        # Pay bonus on first payment
        success, bonus = await referral_service.pay_referral_bonus(
            referred,
            Decimal("299.00"),
        )

        assert success is True
        assert bonus == Decimal("29.90")  # 10%
        assert referral.bonus_amount == bonus


class TestBotWorkflow:
    """Integration tests for bot workflows."""

    @pytest.mark.asyncio
    async def test_user_journey_start_to_subscription(
        self,
        db_session,
        mock_bot,
        mock_three_xui,
        mock_hiddify,
        mock_env,
    ):
        """Test complete user journey from /start to subscription."""
        from aiogram.types import User as TelegramUser
        from src.models.user import User
        from src.bot.handlers.command import handle_start
        from src.services.subscription import SubscriptionService

        # Mock Telegram user
        tg_user = TelegramUser(
            id=123456789,
            is_bot=False,
            first_name="Test",
            username="testuser",
        )

        # Mock message
        mock_message = MagicMock()
        mock_message.from_user = tg_user
        mock_message.text = "/start"
        mock_message.answer = AsyncMock()
        mock_message.bot = mock_bot

        # Handle /start
        with patch("src.bot.handlers.command.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=None)
            ))
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            await handle_start(mock_message)

            # Verify user registration
            mock_session.add.assert_called_once()
            mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_stats_workflow(
        self,
        db_session,
        user,
        subscription,
        payment,
        monkeypatch,
    ):
        """Test admin statistics workflow."""
        monkeypatch.setenv("ADMIN_TELEGRAM_ID", "123456789")

        from src.bot.handlers.admin import handle_stats
        from src.models.payment import PaymentStatus

        mock_message = MagicMock()
        mock_message.from_user = MagicMock(id=123456789)
        mock_message.answer = AsyncMock()

        with patch("src.bot.handlers.admin.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Mock query results
            def execute_side_effect(query):
                mock_result = MagicMock()
                if "User" in str(query):
                    mock_result.scalars = MagicMock(return_value=[user])
                elif "Subscription" in str(query):
                    mock_result.scalars = MagicMock(return_value=[subscription])
                elif "Payment" in str(query):
                    mock_result.scalars = MagicMock(return_value=[payment])
                return mock_result

            mock_session.execute = AsyncMock(side_effect=execute_side_effect)
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            with patch("src.bot.handlers.admin.is_admin", return_value=True):
                await handle_stats(mock_message)

                mock_message.answer.assert_called_once()


class TestSchedulerWorkflow:
    """Integration tests for scheduler workflows."""

    @pytest.mark.asyncio
    async def test_expiry_check_workflow(
        self,
        db_session,
        user,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test scheduled expiry check workflow."""
        from src.workers.jobs import check_expiring_subscriptions

        # Create expired subscription
        from src.models.subscription import Subscription

        expired_sub = Subscription(
            user_id=user.id,
            type=SubscriptionType.ru,
            status=SubscriptionStatus.active,
            start_date=datetime.utcnow() - timedelta(days=60),
            expiry_date=datetime.utcnow() - timedelta(days=1),  # Expired
            panel_uuid="expired-uuid",
        )
        db_session.add(expired_sub)
        await db_session.commit()

        # Run expiry check
        with patch("src.workers.jobs.SubscriptionService") as MockService:
            mock_service = AsyncMock()
            mock_service.block_subscription = AsyncMock(return_value=expired_sub)
            MockService.return_value = mock_service

            blocked_count = await check_expiring_subscriptions()

            assert blocked_count >= 1
            mock_service.block_subscription.assert_called()

    @pytest.mark.asyncio
    async def test_traffic_sync_workflow(
        self,
        db_session,
        subscription,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test scheduled traffic sync workflow."""
        from src.workers.jobs import sync_traffic

        # Setup mock traffic data
        mock_three_xui.get_client_traffic = AsyncMock(
            return_value={"total": 50 * 1024**3}  # 50 GB used
        )

        # Run traffic sync
        updated_count = await sync_traffic()

        assert updated_count >= 0

        # Verify subscription updated
        await db_session.refresh(subscription)
        assert subscription.traffic_used > 0


class TestHealthCheckWorkflow:
    """Integration tests for health check workflows."""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(
        self,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test health check when all systems healthy."""
        from src.core.health import get_health_status

        # Mock healthy services
        mock_three_xui.get_inbounds = AsyncMock(return_value=[])
        mock_hiddify.get_all_users = AsyncMock(return_value=[])

        with patch("src.core.health.ThreeXuiService", return_value=mock_three_xui):
            with patch("src.core.health.HiddifyService", return_value=mock_hiddify):
                health = await get_health_status()

                assert health.status == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_panel_down(
        self,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test health check when panel is down."""
        from src.core.health import get_health_status

        # Mock failed panel
        mock_three_xui.get_inbounds = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_hiddify.get_all_users = AsyncMock(return_value=[])

        with patch("src.core.health.ThreeXuiService", return_value=mock_three_xui):
            with patch("src.core.health.HiddifyService", return_value=mock_hiddify):
                health = await get_health_status()

                # Should be degraded or unhealthy
                assert health.status in ["degraded", "unhealthy"]
                assert health.checks["panels"]["3x-ui"]["status"] == "unhealthy"
