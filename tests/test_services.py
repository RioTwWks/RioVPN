"""Tests for services."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from src.models.referral import Referral
from src.models.user import User
from src.models.subscription import SubscriptionType, SubscriptionStatus
from src.services.subscription import SubscriptionService
from src.services.referral import ReferralService
from src.services.tiers import (
    get_tier,
    get_all_tiers,
    calculate_tier_price,
    format_traffic,
    format_speed,
    TierType,
)


class TestSubscriptionService:
    """Tests for SubscriptionService."""

    @pytest.mark.asyncio
    async def test_create_ru_subscription(
        self,
        db_session,
        user,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test creating RU subscription."""
        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        subscription = await service.create_subscription(
            user=user,
            sub_type=SubscriptionType.ru,
            duration_days=30,
        )

        assert subscription is not None
        assert subscription.type == SubscriptionType.ru
        assert subscription.status == SubscriptionStatus.active
        assert subscription.panel_uuid is not None
        assert subscription.link.startswith("vless://")

        mock_three_xui.add_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_eu_subscription(
        self,
        db_session,
        user,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test creating EU subscription."""
        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        subscription = await service.create_subscription(
            user=user,
            sub_type=SubscriptionType.eu,
            duration_days=30,
        )

        assert subscription is not None
        assert subscription.type == SubscriptionType.eu
        assert subscription.panel_uuid == "test-uuid-123"

        mock_hiddify.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_renew_subscription(
        self,
        db_session,
        subscription,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test subscription renewal."""
        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        original_expiry = subscription.expiry_date
        renewed = await service.renew_subscription(subscription, duration_days=30)

        assert renewed.expiry_date > original_expiry
        assert renewed.status == SubscriptionStatus.active
        assert renewed.traffic_used == 0

    @pytest.mark.asyncio
    async def test_block_subscription(
        self,
        db_session,
        subscription,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test blocking subscription."""
        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        blocked = await service.block_subscription(subscription, reason="expired")

        assert blocked.status == SubscriptionStatus.blocked
        mock_three_xui.delete_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_subscription(
        self,
        db_session,
        user,
        subscription,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test getting user subscription."""
        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        result = await service.get_user_subscription(user)

        assert result is not None
        assert result.id == subscription.id

    @pytest.mark.asyncio
    async def test_sync_traffic(
        self,
        db_session,
        subscription,
        mock_three_xui,
        mock_hiddify,
    ):
        """Test traffic sync."""
        service = SubscriptionService(db_session, mock_three_xui, mock_hiddify)

        updated = await service.sync_traffic()

        assert updated >= 0
        mock_three_xui.get_client_traffic.assert_called()


class TestReferralService:
    """Tests for ReferralService."""

    @pytest.mark.asyncio
    async def test_generate_referral_code(self, db_session, user):
        """Test referral code generation."""
        service = ReferralService(db_session)

        code = service.generate_referral_code(user.telegram_id)

        assert len(code) == 12
        assert code.isupper()

    @pytest.mark.asyncio
    async def test_get_or_create_referral_code(self, db_session, user):
        """Test getting or creating referral code."""
        service = ReferralService(db_session)

        code1 = await service.get_or_create_referral_code(user)
        code2 = await service.get_or_create_referral_code(user)

        assert code1 == code2
        assert len(code1) == 12

    @pytest.mark.asyncio
    async def test_get_referrer_by_code(self, db_session, user):
        """Test finding referrer by code."""
        service = ReferralService(db_session)

        code = await service.get_or_create_referral_code(user)
        referrer = await service.get_referrer_by_code(code)

        assert referrer is not None
        assert referrer.telegram_id == user.telegram_id

    @pytest.mark.asyncio
    async def test_track_referral(self, db_session, user):
        """Test tracking referral."""
        service = ReferralService(db_session)

        referred = User(telegram_id=999888777, username="referred")
        db_session.add(referred)
        await db_session.commit()

        referral = await service.track_referral(user, referred)

        assert referral is not None
        assert referral.referrer_id == user.telegram_id
        assert referral.referred_id == referred.telegram_id

    @pytest.mark.asyncio
    async def test_pay_referral_bonus(self, db_session, user):
        """Test paying referral bonus."""
        service = ReferralService(db_session)

        referred = User(telegram_id=777666555, username="referred")
        db_session.add(referred)
        await db_session.commit()

        await service.track_referral(user, referred)

        success, bonus = await service.pay_referral_bonus(
            referred,
            Decimal("299.00"),
        )

        assert success is True
        assert bonus == Decimal("29.90")  # 10% of 299

    @pytest.mark.asyncio
    async def test_get_referral_stats(self, db_session, user):
        """Test referral statistics."""
        service = ReferralService(db_session)

        # Create referrals
        for i in range(5):
            referred = User(
                telegram_id=100000000 + i,
                username=f"referred{i}",
                referred_by=user.telegram_id,
            )
            db_session.add(referred)
            await db_session.commit()

            referral = Referral(
                referrer_id=user.telegram_id,
                referred_id=referred.telegram_id,
                bonus_amount=Decimal("50.00") if i < 3 else 0,
            )
            db_session.add(referral)
            await db_session.commit()

        stats = await service.get_referral_stats(user)

        assert stats["total_referrals"] == 5
        assert stats["active_referrals"] == 3
        assert stats["total_bonus_earned"] == Decimal("150.00")


class TestTiers:
    """Tests for subscription tiers."""

    def test_get_tier(self):
        """Test getting tier by ID."""
        tier = get_tier(TierType.PREMIUM)

        assert tier.id == TierType.PREMIUM
        assert tier.name == "Премиум"
        assert tier.devices == 3

    def test_get_all_tiers(self):
        """Test getting all tiers."""
        tiers = get_all_tiers()

        assert len(tiers) == 3
        tier_ids = [t.id for t in tiers]
        assert TierType.BASIC in tier_ids
        assert TierType.PREMIUM in tier_ids
        assert TierType.UNLIMITED in tier_ids

    def test_calculate_tier_price(self):
        """Test tier price calculation."""
        tier = get_tier(TierType.BASIC)
        base_price = Decimal("299.00")

        price = calculate_tier_price(base_price, tier)

        assert price == Decimal("239.20")  # 299 * 0.8

    def test_format_traffic(self):
        """Test traffic formatting."""
        assert format_traffic(50 * 1024**3) == "50 ГБ"
        assert format_traffic(500 * 1024**2) == "500 МБ"
        assert format_traffic(None) == "Безлимитный"

    def test_format_speed(self):
        """Test speed formatting."""
        assert format_speed(100) == "100 Мбит/с"
        assert format_speed(None) == "Без ограничений"

    def test_tier_features(self):
        """Test tier features."""
        basic = get_tier(TierType.BASIC)
        unlimited = get_tier(TierType.UNLIMITED)

        assert basic.traffic_limit is not None
        assert unlimited.traffic_limit is None

        assert basic.speed_limit is not None
        assert unlimited.speed_limit is None

        assert basic.devices == 1
        assert unlimited.devices == 5
