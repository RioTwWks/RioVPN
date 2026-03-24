"""Subscription tiers configuration."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional


class TierType(str, Enum):
    """Subscription tier types."""

    BASIC = "basic"
    PREMIUM = "premium"
    UNLIMITED = "unlimited"


@dataclass
class SubscriptionTier:
    """
    Subscription tier configuration.

    Attributes:
        id: Tier identifier
        name: Display name
        traffic_limit: Traffic limit in bytes (None = unlimited)
        speed_limit: Speed limit in Mbps (None = unlimited)
        devices: Number of allowed devices
        price_multiplier: Price multiplier (1.0 = base price)
        features: List of feature descriptions
    """

    id: TierType
    name: str
    traffic_limit: Optional[int]  # in bytes
    speed_limit: Optional[int]  # in Mbps
    devices: int
    price_multiplier: Decimal
    features: List[str]


# Tier configurations
SUBSCRIPTION_TIERS: Dict[TierType, SubscriptionTier] = {
    TierType.BASIC: SubscriptionTier(
        id=TierType.BASIC,
        name="Базовый",
        traffic_limit=50 * 1024**3,  # 50 GB
        speed_limit=50,  # 50 Mbps
        devices=1,
        price_multiplier=Decimal("0.8"),  # 20% discount
        features=[
            "50 ГБ трафика в месяц",
            "Скорость до 50 Мбит/с",
            "1 устройство",
            "Россия (RU)",
        ],
    ),
    TierType.PREMIUM: SubscriptionTier(
        id=TierType.PREMIUM,
        name="Премиум",
        traffic_limit=200 * 1024**3,  # 200 GB
        speed_limit=100,  # 100 Mbps
        devices=3,
        price_multiplier=Decimal("1.0"),  # Base price
        features=[
            "200 ГБ трафика в месяц",
            "Скорость до 100 Мбит/с",
            "3 устройства",
            "Россия (RU) + Европа (EU)",
            "Приоритетная поддержка",
        ],
    ),
    TierType.UNLIMITED: SubscriptionTier(
        id=TierType.UNLIMITED,
        name="Безлимитный",
        traffic_limit=None,  # Unlimited
        speed_limit=None,  # No speed limit
        devices=5,
        price_multiplier=Decimal("1.5"),  # 50% premium
        features=[
            "Безлимитный трафик",
            "Максимальная скорость",
            "5 устройств",
            "Россия (RU) + Европа (EU)",
            "Приоритетная поддержка",
            "Ранний доступ к новым функциям",
        ],
    ),
}


def get_tier(tier_id: TierType) -> SubscriptionTier:
    """
    Get tier configuration.

    Args:
        tier_id: Tier identifier

    Returns:
        SubscriptionTier configuration
    """
    return SUBSCRIPTION_TIERS.get(tier_id, SUBSCRIPTION_TIERS[TierType.PREMIUM])


def get_all_tiers() -> List[SubscriptionTier]:
    """
    Get all tier configurations.

    Returns:
        List of all subscription tiers
    """
    return list(SUBSCRIPTION_TIERS.values())


def calculate_tier_price(
    base_price: Decimal,
    tier: SubscriptionTier,
) -> Decimal:
    """
    Calculate price for tier.

    Args:
        base_price: Base subscription price
        tier: Tier configuration

    Returns:
        Tier price
    """
    return (base_price * tier.price_multiplier).quantize(Decimal("0.01"))


def format_traffic(traffic_bytes: Optional[int]) -> str:
    """
    Format traffic limit for display.

    Args:
        traffic_bytes: Traffic in bytes

    Returns:
        Formatted traffic string
    """
    if traffic_bytes is None:
        return "Безлимитный"

    if traffic_bytes >= 1024**3:
        gb = traffic_bytes / (1024**3)
        return f"{gb:.0f} ГБ"
    elif traffic_bytes >= 1024**2:
        mb = traffic_bytes / (1024**2)
        return f"{mb:.0f} МБ"
    else:
        return f"{traffic_bytes} Б"


def format_speed(speed_mbps: Optional[int]) -> str:
    """
    Format speed limit for display.

    Args:
        speed_mbps: Speed in Mbps

    Returns:
        Formatted speed string
    """
    if speed_mbps is None:
        return "Без ограничений"
    return f"{speed_mbps} Мбит/с"
