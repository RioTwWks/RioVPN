"""Subscription model and enums."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class SubscriptionType(str, enum.Enum):
    """Subscription type enumeration."""

    ru = "ru"  # Russian VPS via 3x-ui
    eu = "eu"  # European VPS via Hiddify


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration."""

    active = "active"
    expired = "expired"
    blocked = "blocked"


class Subscription(Base):
    """
    Subscription model representing VPN subscriptions.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        type: Subscription type (ru/eu)
        status: Subscription status (active/expired/blocked)
        start_date: Subscription start date
        expiry_date: Subscription expiry date
        traffic_limit: Traffic limit in bytes (None = unlimited)
        traffic_used: Used traffic in bytes
        panel_uuid: User UUID in panel (Hiddify) or email (3x-ui)
        inbound_tag: 3x-ui inbound tag
        link: vless:// subscription link
    """

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type = Column(
        Enum(SubscriptionType, name="sub_type"),
        nullable=False
    )
    status = Column(
        Enum(SubscriptionStatus, name="sub_status"),
        default=SubscriptionStatus.active,
        nullable=False
    )
    start_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    traffic_limit = Column(BigInteger, nullable=True)
    traffic_used = Column(BigInteger, default=0, nullable=False)
    panel_uuid = Column(String(64), nullable=True)
    inbound_tag = Column(String(64), nullable=True)
    link = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<Subscription(id={self.id}, user_id={self.user_id}, "
            f"type={self.type.value}, status={self.status.value})>"
        )

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == SubscriptionStatus.active

    @property
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        return datetime.utcnow() > self.expiry_date

    @property
    def days_remaining(self) -> int:
        """Get remaining days until expiry."""
        delta = self.expiry_date - datetime.utcnow()
        return max(0, delta.days)

    @property
    def traffic_remaining(self) -> Optional[int]:
        """Get remaining traffic in bytes."""
        if self.traffic_limit is None:
            return None
        return max(0, self.traffic_limit - self.traffic_used)

    @property
    def traffic_used_percent(self) -> float:
        """Get percentage of traffic used."""
        if self.traffic_limit is None:
            return 0.0
        if self.traffic_limit == 0:
            return 100.0
        return min(100.0, (self.traffic_used / self.traffic_limit) * 100)
