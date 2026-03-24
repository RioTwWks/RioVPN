"""Referral service for managing referrals."""

import hashlib
import logging
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import select

from src.core.database import AsyncSession
from src.models.referral import Referral
from src.models.user import User

logger = logging.getLogger(__name__)

# Referral bonus configuration
REFERRAL_BONUS_PERCENT = Decimal("0.10")  # 10% of first payment
MAX_BONUS_AMOUNT = Decimal("500")  # Maximum bonus in RUB


class ReferralService:
    """
    Service for managing user referrals.

    Handles:
    - Referral code generation
    - Referral tracking
    - Bonus payments
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize referral service.

        Args:
            session: Database session
        """
        self.session = session

    def generate_referral_code(self, telegram_id: int) -> str:
        """
        Generate unique referral code for user.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            Unique referral code
        """
        # Create hash from telegram_id + timestamp
        data = f"{telegram_id}_{telegram_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:12].upper()

    async def get_or_create_referral_code(self, user: User) -> str:
        """
        Get existing or create new referral code.

        Args:
            user: User instance

        Returns:
            Referral code
        """
        if user.referral_code:
            return user.referral_code

        # Generate and save new code
        referral_code = self.generate_referral_code(user.telegram_id)
        user.referral_code = referral_code
        await self.session.commit()

        logger.info(f"Generated referral code {referral_code} for user {user.telegram_id}")
        return referral_code

    async def get_referrer_by_code(
        self,
        referral_code: str,
    ) -> Optional[User]:
        """
        Get referrer user by referral code.

        Args:
            referral_code: Referral code

        Returns:
            Referrer user or None
        """
        result = await self.session.execute(select(User).where(User.referral_code == referral_code))
        return result.scalar_one_or_none()

    async def track_referral(
        self,
        referrer: User,
        referred: User,
    ) -> Optional[Referral]:
        """
        Track a new referral.

        Args:
            referrer: User who referred
            referred: User who was referred

        Returns:
            Created referral or None if already exists
        """
        # Check if already referred
        existing = await self.session.execute(select(Referral).where(Referral.referred_id == referred.telegram_id))
        if existing.scalar_one_or_none():
            logger.warning(f"Referral already exists for user {referred.telegram_id}")
            return None

        # Create referral record
        referral = Referral(
            referrer_id=referrer.telegram_id,
            referred_id=referred.telegram_id,
            bonus_amount=0,  # Will be set on first payment
        )

        # Update referred user
        referred.referred_by = referrer.telegram_id

        self.session.add(referral)
        await self.session.commit()

        logger.info(f"Referral tracked: {referrer.telegram_id} -> {referred.telegram_id}")

        return referral

    async def pay_referral_bonus(
        self,
        referred_user: User,
        payment_amount: Decimal,
    ) -> Tuple[bool, Decimal]:
        """
        Pay referral bonus to referrer.

        Args:
            referred_user: User who made the payment
            payment_amount: Payment amount

        Returns:
            Tuple of (success, bonus_amount)
        """
        # Find referral
        result = await self.session.execute(select(Referral).where(Referral.referred_id == referred_user.telegram_id))
        referral = result.scalar_one_or_none()

        if not referral:
            return False, Decimal("0")

        # Check if bonus already paid
        if referral.bonus_amount > 0:
            logger.warning(f"Bonus already paid for referral {referral.id}")
            return False, Decimal("0")

        # Calculate bonus
        bonus = payment_amount * REFERRAL_BONUS_PERCENT
        bonus = min(bonus, MAX_BONUS_AMOUNT)  # Cap at maximum

        # Update referral with bonus
        referral.bonus_amount = bonus

        # Note: In production, you would:
        # 1. Create wallet/balance record for referrer
        # 2. Add bonus to their account
        # 3. Send notification

        logger.info(f"Referral bonus paid: {bonus} RUB to {referral.referrer_id} " f"(from {referred_user.telegram_id})")

        return True, bonus

    async def get_referral_stats(
        self,
        user: User,
    ) -> dict:
        """
        Get referral statistics for user.

        Args:
            user: User instance

        Returns:
            Dictionary with referral stats
        """
        # Count referrals
        result = await self.session.execute(select(Referral).where(Referral.referrer_id == user.telegram_id))
        referrals = result.scalars().all()

        total_referrals = len(referrals)
        total_bonus = sum(r.bonus_amount for r in referrals)
        active_referrals = sum(1 for r in referrals if r.bonus_amount > 0)

        return {
            "total_referrals": total_referrals,
            "active_referrals": active_referrals,
            "total_bonus_earned": total_bonus,
        }
