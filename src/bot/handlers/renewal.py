"""Renewal handlers for the bot."""

import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from src.bot.keyboards import get_back_keyboard
from src.bot.notifications import get_notification_service
from src.core.database import get_session
from src.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from src.models.user import User
from src.services.payment.base import PaymentData
from src.services.payment.provider import get_available_payment_providers, get_payment_provider

logger = logging.getLogger(__name__)

renewal_router = Router()

# Price configuration (RUB)
PRICES = {
    "ru": {
        1: Decimal("299"),
        3: Decimal("799"),
        6: Decimal("1499"),
        12: Decimal("2699"),
    },
    "eu": {
        1: Decimal("499"),
        3: Decimal("1299"),
        6: Decimal("2399"),
        12: Decimal("4299"),
    },
}


@renewal_router.callback_query(F.data.startswith("renew_sub_"))
async def handle_renewal_start(callback: CallbackQuery) -> None:
    """
    Handle renewal start - show subscription details.

    Args:
        callback: Callback query
    """
    # Parse: renew_sub_123
    parts = callback.data.split("_")
    subscription_id = int(parts[2])

    async for session in get_session():
        # Get subscription
        result = await session.execute(select(Subscription).where(Subscription.id == subscription_id))
        subscription = result.scalar_one_or_none()

        if not subscription:
            await callback.answer("❌ Подписка не найдена", show_alert=True)
            return

        # Check ownership
        user_result = await session.execute(select(User).where(User.id == subscription.user_id))
        user = user_result.scalar_one_or_none()

        if not user or user.telegram_id != callback.from_user.id:
            await callback.answer("❌ Доступ запрещён", show_alert=True)
            return

        # Check if active
        if subscription.status != SubscriptionStatus.active:
            await callback.answer(
                "❌ Нельзя продлить неактивную подписку",
                show_alert=True,
            )
            return

        # Show renewal options
        type_emoji = "🇷🇺" if subscription.type.value == "ru" else "🇪🇺"

        await callback.message.edit_text(
            f"💳 <b>Продление подписки</b>\n\n"
            f"{type_emoji} <b>Тип:</b> {subscription.type.value.upper()}\n"
            f"📅 <b>Действует до:</b> {subscription.expiry_date.strftime('%d.%m.%Y')}\n"
            f"⏳ <b>Осталось дней:</b> {subscription.days_remaining}\n\n"
            f"Выберите срок продления:",
            reply_markup=get_renewal_duration_keyboard(subscription.id, subscription.type.value),
        )

    await callback.answer()


@renewal_router.callback_query(F.data.startswith("renew_duration_"))
async def handle_renewal_duration(callback: CallbackQuery) -> None:
    """
    Handle renewal duration selection.

    Args:
        callback: Callback query
    """
    # Parse: renew_duration_1_ru_123
    parts = callback.data.split("_")
    subscription_id = int(parts[3])
    sub_type = parts[2]
    duration = int(parts[4])

    async for session in get_session():
        # Get subscription
        result = await session.execute(select(Subscription).where(Subscription.id == subscription_id))
        subscription = result.scalar_one_or_none()

        if not subscription:
            await callback.answer("❌ Подписка не найдена", show_alert=True)
            return

        # Get available payment providers
        providers = get_available_payment_providers(session)

        if not providers:
            await callback.answer(
                "⚠️ Платежные системы временно недоступны",
                show_alert=True,
            )
            return

        # Build payment provider keyboard
        builder = InlineKeyboardBuilder()

        for provider in providers:
            provider_name = get_provider_name(provider)
            builder.button(
                text=f"💳 {provider_name}", callback_data=f"renew_pay_{subscription_id}_{sub_type}_{duration}_{provider}"
            )

        builder.button(text="« Назад", callback_data=f"renew_sub_{subscription_id}")
        builder.adjust(1)

        price = PRICES.get(sub_type, {}).get(duration, Decimal("0"))

        await callback.message.edit_text(
            f"💳 <b>Продление подписки</b>\n\n"
            f"⏳ <b>Срок:</b> {duration} мес.\n"
            f"💰 <b>Стоимость:</b> {price} ₽\n\n"
            f"Выберите платежную систему:",
            reply_markup=builder.as_markup(),
        )

    await callback.answer()


@renewal_router.callback_query(F.data.startswith("renew_pay_"))
async def handle_renewal_payment(callback: CallbackQuery) -> None:
    """
    Handle renewal payment creation.

    Args:
        callback: Callback query
    """
    # Parse: renew_pay_123_ru_3_cryptomus
    parts = callback.data.split("_")
    subscription_id = int(parts[2])
    sub_type = parts[3]
    duration = int(parts[4])
    provider = parts[5]

    async for session in get_session():
        # Get subscription
        result = await session.execute(select(Subscription).where(Subscription.id == subscription_id))
        subscription = result.scalar_one_or_none()

        if not subscription:
            await callback.answer("❌ Подписка не найдена", show_alert=True)
            return

        # Get user
        user_result = await session.execute(select(User).where(User.id == subscription.user_id))
        user = user_result.scalar_one_or_none()

        if not user or user.telegram_id != callback.from_user.id:
            await callback.answer("❌ Доступ запрещён", show_alert=True)
            return

        # Get payment service
        payment_service = get_payment_provider(session, provider)

        if not payment_service:
            await callback.answer(
                "⚠️ Платежная система недоступна",
                show_alert=True,
            )
            return

        # Create payment for renewal
        price = PRICES.get(sub_type, {}).get(duration, Decimal("0"))
        payment_data = PaymentData(
            amount=price,
            currency="RUB",
            user_id=user.id,
            subscription_type=subscription.type,
            duration_months=duration,
            description=f"Renewal: {sub_type}_{duration}_{subscription_id}",
        )

        result = await payment_service.create_payment(payment_data)

        if not result.success:
            await callback.message.edit_text(
                "❌ <b>Ошибка создания платежа</b>\n\n"
                f"Причина: {result.error_message}\n\n"
                "Попробуйте позже или выберите другой способ оплаты.",
                reply_markup=get_back_keyboard(),
            )
            return

        # Send payment link
        provider_name = get_provider_name(provider)

        await callback.message.edit_text(
            f"✅ <b>Платеж создан</b>\n\n"
            f"💳 <b>Сумма:</b> {price} ₽\n"
            f"🏦 <b>Платежная система:</b> {provider_name}\n\n"
            f"Нажмите кнопку ниже для оплаты:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="💰 Оплатить",
                            url=result.payment_url,
                        )
                    ]
                ]
            ),
        )

    await callback.answer()


def get_renewal_duration_keyboard(
    subscription_id: int,
    sub_type: str,
) -> InlineKeyboardMarkup:
    """
    Get renewal duration selection keyboard.

    Args:
        subscription_id: Subscription ID
        sub_type: Subscription type (ru/eu)

    Returns:
        InlineKeyboardMarkup with duration options
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="1 месяц", callback_data=f"renew_duration_{subscription_id}_{sub_type}_1")
    builder.button(text="3 месяца", callback_data=f"renew_duration_{subscription_id}_{sub_type}_3")
    builder.button(text="6 месяцев", callback_data=f"renew_duration_{subscription_id}_{sub_type}_6")
    builder.button(text="12 месяцев", callback_data=f"renew_duration_{subscription_id}_{sub_type}_12")
    builder.button(text="« Назад", callback_data="main_menu")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_provider_name(provider: str) -> str:
    """
    Get human-readable provider name.

    Args:
        provider: Provider identifier

    Returns:
        Provider name
    """
    names = {
        "cryptomus": "Cryptomus (Crypto)",
        "yookassa": "ЮKassa (Карты РФ)",
        "telegram_stars": "Telegram Stars",
    }
    return names.get(provider, provider)
