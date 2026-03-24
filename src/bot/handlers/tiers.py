"""Subscription tier selection handlers."""

import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.database import get_session
from src.services.tiers import (
    TierType,
    get_all_tiers,
    get_tier,
    calculate_tier_price,
    format_traffic,
    format_speed,
)

logger = logging.getLogger(__name__)

tier_router = Router()

# Base prices (RUB)
BASE_PRICES = {
    "ru": {1: Decimal("299"), 3: Decimal("799"), 6: Decimal("1499"), 12: Decimal("2699")},
    "eu": {1: Decimal("499"), 3: Decimal("1299"), 6: Decimal("2399"), 12: Decimal("4299")},
}


@tier_router.callback_query(F.data == "select_tier")
async def handle_tier_selection(callback: CallbackQuery) -> None:
    """
    Handle tier selection.

    Args:
        callback: Callback query
    """
    tiers = get_all_tiers()

    builder = InlineKeyboardBuilder()
    for tier in tiers:
        builder.button(text=f"💎 {tier.name}", callback_data=f"tier_{tier.id.value}")

    builder.button(text="« Назад", callback_data="select_type")
    builder.adjust(1)

    await callback.message.edit_text(
        "💎 <b>Выберите тариф</b>\n\n"
        "Все тарифы включают:\n"
        "• Мгновенная активация\n"
        "• Поддержка 24/7\n"
        "• Гарантия возврата\n\n"
        "Выберите подходящий тариф:",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@tier_router.callback_query(F.data.startswith("tier_"))
async def handle_tier_details(callback: CallbackQuery) -> None:
    """
    Handle tier details view.

    Args:
        callback: Callback query
    """
    tier_id = TierType(callback.data.split("_")[1])
    tier = get_tier(tier_id)

    # Parse sub_type and duration from callback data or use defaults
    sub_type = "ru"  # Default, would be passed in real implementation
    duration = 1

    base_price = BASE_PRICES.get(sub_type, {}).get(duration, Decimal("299"))
    tier_price = calculate_tier_price(base_price, tier)

    features_text = "\n".join(f"• {f}" for f in tier.features)

    builder = InlineKeyboardBuilder()
    builder.button(text=f"💰 Выбрать ({tier_price} ₽)", callback_data=f"pay_tier_{tier_id.value}_{sub_type}_{duration}")
    builder.button(text="« Назад к тарифам", callback_data="select_tier")
    builder.button(text="« Назад", callback_data="select_type")
    builder.adjust(1, 1)

    text = (
        f"💎 <b>Тариф: {tier.name}</b>\n\n"
        f"📊 <b>Характеристики:</b>\n"
        f"• Трафик: {format_traffic(tier.traffic_limit)}\n"
        f"• Скорость: {format_speed(tier.speed_limit)}\n"
        f"• Устройств: {tier.devices}\n\n"
        f"📋 <b>Включено:</b>\n"
        f"{features_text}\n\n"
        f"💰 <b>Цена:</b> {tier_price} ₽/мес"
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


def get_tier_keyboard(
    sub_type: str,
    duration: int,
) -> InlineKeyboardMarkup:
    """
    Get tier selection keyboard.

    Args:
        sub_type: Subscription type (ru/eu)
        duration: Duration in months

    Returns:
        InlineKeyboardMarkup with tier options
    """
    tiers = get_all_tiers()
    builder = InlineKeyboardBuilder()

    for tier in tiers:
        base_price = BASE_PRICES.get(sub_type, {}).get(duration, Decimal("299"))
        tier_price = calculate_tier_price(base_price, tier)
        builder.button(text=f"💎 {tier.name} - {tier_price} ₽", callback_data=f"tier_{tier.id.value}_{sub_type}_{duration}")

    builder.button(text="« Назад", callback_data="select_type")
    builder.adjust(1)
    return builder.as_markup()
