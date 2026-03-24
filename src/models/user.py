"""User model for Telegram users."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.referral import Referral
    from src.models.subscription import Subscription


class User(Base):
    """
    User model representing Telegram users.

    Attributes:
        id: Primary key
        telegram_id: Unique Telegram user ID
        username: Telegram username
        created_at: Account creation timestamp
        referral_code: Unique referral code for this user
        referred_by: Telegram ID of user who referred this user
        subscriptions: Related subscriptions
        referrals: Users referred by this user
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    referral_code = Column(String(32), unique=True, nullable=True, index=True)
    referred_by = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)

    # Relationships
    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    payments = relationship(
        "Payment",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    referrals = relationship(
        "Referral",
        back_populates="referrer",
        lazy="selectin",
        cascade="all, delete-orphan",
        foreign_keys="Referral.referrer_id"
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
