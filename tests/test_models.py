"""Tests for database models."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.models.user import User
from src.models.subscription import Subscription, SubscriptionType, SubscriptionStatus
from src.models.payment import Payment, PaymentProvider, PaymentStatus
from src.models.referral import Referral


class TestUserModel:
    """Tests for User model."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test user creation."""
        user = User(
            telegram_id=987654321,
            username="newuser",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.telegram_id == 987654321
        assert user.username == "newuser"
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_user_unique_telegram_id(self, db_session):
        """Test telegram_id uniqueness."""
        user1 = User(telegram_id=111111111, username="user1")
        db_session.add(user1)
        await db_session.commit()

        user2 = User(telegram_id=111111111, username="user2")
        db_session.add(user2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_relationships(self, db_session, user, subscription, payment):
        """Test user relationships."""
        # Refresh to get relationships
        await db_session.refresh(user)

        assert len(user.subscriptions) == 1
        assert len(user.payments) == 1
        assert user.subscriptions[0].id == subscription.id
        assert user.payments[0].id == payment.id

    def test_user_repr(self, user):
        """Test user string representation."""
        assert str(user.id) in repr(user)
        assert str(user.telegram_id) in repr(user)


class TestSubscriptionModel:
    """Tests for Subscription model."""

    @pytest.mark.asyncio
    async def test_create_subscription(self, db_session, user):
        """Test subscription creation."""
        subscription = Subscription(
            user_id=user.id,
            type=SubscriptionType.eu,
            status=SubscriptionStatus.active,
            start_date=datetime.utcnow(),
            expiry_date=datetime.utcnow() + timedelta(days=30),
            traffic_limit=50 * 1024**3,
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        assert subscription.id is not None
        assert subscription.type == SubscriptionType.eu
        assert subscription.status == SubscriptionStatus.active
        assert subscription.traffic_limit == 50 * 1024**3

    def test_subscription_is_active(self, subscription):
        """Test is_active property."""
        assert subscription.is_active is True

        subscription.status = SubscriptionStatus.blocked
        assert subscription.is_active is False

    def test_subscription_is_expired(self, subscription):
        """Test is_expired property."""
        assert subscription.is_expired is False

        subscription.expiry_date = datetime.utcnow() - timedelta(days=1)
        assert subscription.is_expired is True

    def test_subscription_days_remaining(self, subscription):
        """Test days_remaining property."""
        subscription.expiry_date = datetime.utcnow() + timedelta(days=15)
        assert subscription.days_remaining == 15

        subscription.expiry_date = datetime.utcnow() - timedelta(days=5)
        assert subscription.days_remaining == 0

    def test_subscription_traffic_remaining(self, subscription):
        """Test traffic_remaining property."""
        subscription.traffic_limit = 100 * 1024**3
        subscription.traffic_used = 30 * 1024**3

        remaining = subscription.traffic_remaining
        assert remaining == 70 * 1024**3

    def test_subscription_traffic_used_percent(self, subscription):
        """Test traffic_used_percent property."""
        subscription.traffic_limit = 100 * 1024**3
        subscription.traffic_used = 75 * 1024**3

        assert subscription.traffic_used_percent == 75.0

        # Test unlimited
        subscription.traffic_limit = None
        assert subscription.traffic_used_percent == 0.0

    def test_subscription_repr(self, subscription):
        """Test subscription string representation."""
        assert str(subscription.id) in repr(subscription)
        assert subscription.type.value in repr(subscription)


class TestPaymentModel:
    """Tests for Payment model."""

    @pytest.mark.asyncio
    async def test_create_payment(self, db_session, user):
        """Test payment creation."""
        payment = Payment(
            user_id=user.id,
            amount=Decimal("499.00"),
            currency="RUB",
            status=PaymentStatus.pending,
            provider=PaymentProvider.yookassa,
            external_id="yookassa-123",
        )
        db_session.add(payment)
        await db_session.commit()
        await db_session.refresh(payment)

        assert payment.id is not None
        assert payment.amount == Decimal("499.00")
        assert payment.status == PaymentStatus.pending
        assert payment.provider == PaymentProvider.yookassa

    def test_payment_repr(self, payment):
        """Test payment string representation."""
        assert str(payment.id) in repr(payment)
        assert str(payment.amount) in repr(payment)


class TestReferralModel:
    """Tests for Referral model."""

    @pytest.mark.asyncio
    async def test_create_referral(self, db_session, user):
        """Test referral creation."""
        referred_user = User(telegram_id=999999999, username="referred")
        db_session.add(referred_user)
        await db_session.commit()

        referral = Referral(
            referrer_id=user.telegram_id,
            referred_id=referred_user.telegram_id,
            bonus_amount=Decimal("50.00"),
        )
        db_session.add(referral)
        await db_session.commit()
        await db_session.refresh(referral)

        assert referral.id is not None
        assert referral.referrer_id == user.telegram_id
        assert referral.referred_id == referred_user.telegram_id
        assert referral.bonus_amount == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_referral_unique_referred_id(self, db_session, user):
        """Test referred_id uniqueness."""
        referred_user1 = User(telegram_id=111222333, username="ref1")
        referred_user2 = User(telegram_id=444555666, username="ref2")
        db_session.add_all([referred_user1, referred_user2])
        await db_session.commit()

        referral1 = Referral(
            referrer_id=user.telegram_id,
            referred_id=referred_user1.telegram_id,
        )
        db_session.add(referral1)
        await db_session.commit()

        referral2 = Referral(
            referrer_id=user.telegram_id,
            referred_id=referred_user1.telegram_id,  # Same referred_id
        )
        db_session.add(referral2)

        with pytest.raises(Exception):
            await db_session.commit()

    def test_referral_repr(self, referral):
        """Test referral string representation."""
        assert str(referral.id) in repr(referral)
        assert str(referral.referrer_id) in repr(referral)
