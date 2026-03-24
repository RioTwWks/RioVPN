"""Referral model for tracking referrals."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class Referral(Base):
    """
    Referral model for tracking user referrals.

    Attributes:
        id: Primary key
        referrer_id: User who referred (Telegram ID)
        referred_id: User who was referred (Telegram ID)
        bonus_amount: Bonus paid to referrer
        created_at: Referral timestamp
        referrer: Referrer user relationship
    """

    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        nullable=False,
        index=True
    )
    referred_id = Column(BigInteger, nullable=False, unique=True, index=True)
    bonus_amount = Column(Numeric(10, 2), default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    referrer = relationship(
        "User",
        back_populates="referrals",
        foreign_keys=[referrer_id]
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<Referral(id={self.id}, referrer={self.referrer_id}, "
            f"referred={self.referred_id})>"
        )
