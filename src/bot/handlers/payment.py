"""Payment handlers for the bot."""

import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.database import get_session
from src.models.subscription import SubscriptionType
from src.services.payment.base import PaymentData
from src.services.payment.provider import get_available_payment_providers, get_payment_provider

logger = logging.getLogger(__name__)

payment_router = Router()

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


@payment_router.callback_query(F.data.startswith("pay_"))
async def handle_payment_selection(callback: CallbackQuery) -> None:
    """
    Handle payment method selection.

    Args:
        callback: Callback query
    """
    # Parse: pay_ru_3
    parts = callback.data.split("_")
    sub_type = parts[1]
    duration = int(parts[2])

    async for session in get_session():
        # Get available payment providers
        providers = get_available_payment_providers(session)

        if not providers:
            await callback.answer(
                "⚠️ Платежные системы временно недоступны. " "Попробуйте позже или обратитесь в поддержку.",
                show_alert=True,
            )
            return

        # Build payment provider keyboard
        builder = InlineKeyboardBuilder()

        for provider in providers:
            provider_name = get_provider_name(provider)
            builder.button(text=f"💳 {provider_name}", callback_data=f"pay_provider_{sub_type}_{duration}_{provider}")

        builder.button(text="« Назад", callback_data="select_type")
        builder.adjust(1)

        price = PRICES.get(sub_type, {}).get(duration, Decimal("0"))
        type_name = "Россия (RU)" if sub_type == "ru" else "Европа (EU)"

        await callback.message.edit_text(
            f"💳 <b>Выберите способ оплаты</b>\n\n"
            f"📍 Тип: {type_name}\n"
            f"⏳ Срок: {duration} мес.\n"
            f"💰 Стоимость: <b>{price} ₽</b>\n\n"
            f"Выберите платежную систему:",
            reply_markup=builder.as_markup(),
        )

    await callback.answer()


@payment_router.callback_query(F.data.startswith("pay_provider_"))
async def handle_payment_provider(callback: CallbackQuery) -> None:
    """
    Handle payment provider selection and create payment.

    Args:
        callback: Callback query
    """
    # Parse: pay_provider_ru_3_cryptomus
    parts = callback.data.split("_")
    sub_type = parts[2]
    duration = int(parts[3])
    provider = parts[4]

    async for session in get_session():
        # Get user
        from sqlalchemy import select
        from src.models.user import User

        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        # Get payment service
        payment_service = get_payment_provider(session, provider)

        if not payment_service:
            await callback.answer(
                "⚠️ Платежная система недоступна",
                show_alert=True,
            )
            return

        # Create payment
        price = PRICES.get(sub_type, {}).get(duration, Decimal("0"))
        payment_data = PaymentData(
            amount=price,
            currency="RUB",
            user_id=user.id,
            subscription_type=SubscriptionType(sub_type),
            duration_months=duration,
            description=f"Subscription: {sub_type}_{duration}",
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

        await callback.message.answer(
            "⏳ <b>Ожидаем оплату...</b>\n\n"
            "После успешной оплаты подписка будет активирована автоматически.\n"
            "Я отправлю вам уведомление."
        )

    await callback.answer()


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


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Get back button keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="« Назад в меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
