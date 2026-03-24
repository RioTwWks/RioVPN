"""Payment model and enums."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""

    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class PaymentProvider(str, enum.Enum):
    """Payment provider enumeration."""

    cryptomus = "cryptomus"
    yookassa = "yookassa"
    telegram_stars = "telegram_stars"
    manual = "manual"


class Payment(Base):
    """
    Payment model representing payment transactions.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        amount: Payment amount
        currency: Payment currency (RUB, USD, EUR)
        status: Payment status
        provider: Payment provider
        external_id: External payment ID (from payment gateway)
        description: Payment description
        created_at: Payment creation timestamp
        updated_at: Payment update timestamp
    """

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="RUB", nullable=False)
    status = Column(Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.pending, nullable=False)
    provider = Column(Enum(PaymentProvider, name="payment_provider"), nullable=False)
    external_id = Column(String(255), nullable=True, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount} {self.currency}, status={self.status.value})>"
        )
