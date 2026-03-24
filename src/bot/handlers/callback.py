"""Callback query handlers for inline keyboards."""

import logging
from datetime import timedelta
from typing import Optional

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from src.bot.keyboards import (
    get_back_keyboard,
    get_payment_keyboard,
    get_start_keyboard,
    get_subscription_duration_keyboard,
    get_subscription_type_keyboard,
)
from src.core.config import settings
from src.core.database import get_session
from src.models.subscription import Subscription, SubscriptionType
from src.models.user import User
from src.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)

callback_router = Router()

# Price configuration (RUB)
PRICES = {
    "ru": {
        1: 299,
        3: 799,
        6: 1499,
        12: 2699,
    },
    "eu": {
        1: 499,
        3: 1299,
        6: 2399,
        12: 4299,
    },
}


@callback_router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery) -> None:
    """
    Handle main menu button.

    Args:
        callback: Callback query
    """
    await callback.message.edit_text(
        "👋 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        reply_markup=get_start_keyboard(),
    )
    await callback.answer()


@callback_router.callback_query(F.data == "buy")
async def handle_buy(callback: CallbackQuery) -> None:
    """
    Handle buy button - show subscription types.

    Args:
        callback: Callback query
    """
    await callback.message.edit_text(
        "🛒 <b>Покупка подписки</b>\n\n"
        "Выберите тип подписки:",
        reply_markup=get_subscription_type_keyboard(),
    )
    await callback.answer()


@callback_router.callback_query(F.data == "select_type")
async def handle_select_type(callback: CallbackQuery) -> None:
    """
    Handle back to type selection.

    Args:
        callback: Callback query
    """
    await callback.message.edit_text(
        "🛒 <b>Покупка подписки</b>\n\n"
        "Выберите тип подписки:",
        reply_markup=get_subscription_type_keyboard(),
    )
    await callback.answer()


@callback_router.callback_query(F.data == "sub_type_ru")
async def handle_sub_type_ru(callback: CallbackQuery) -> None:
    """
    Handle Russia subscription type selection.

    Args:
        callback: Callback query
    """
    await callback.message.edit_text(
        "🇷🇺 <b>Россия (RU)</b>\n\n"
        "Подключение к российскому серверу для обхода белых списков.\n\n"
        "Выберите срок подписки:",
        reply_markup=get_subscription_duration_keyboard("ru"),
    )
    await callback.answer()


@callback_router.callback_query(F.data == "sub_type_eu")
async def handle_sub_type_eu(callback: CallbackQuery) -> None:
    """
    Handle Europe subscription type selection.

    Args:
        callback: Callback query
    """
    await callback.message.edit_text(
        "🇪🇺 <b>Европа (EU)</b>\n\n"
        "Подключение к европейскому серверу для выхода в мировой интернет.\n\n"
        "Выберите срок подписки:",
        reply_markup=get_subscription_duration_keyboard("eu"),
    )
    await callback.answer()


@callback_router.callback_query(F.data.startswith("duration_"))
async def handle_duration(callback: CallbackQuery) -> None:
    """
    Handle duration selection.

    Args:
        callback: Callback query
    """
    # Parse: duration_ru_3
    parts = callback.data.split("_")
    sub_type = parts[1]
    duration = int(parts[2])

    price = PRICES.get(sub_type, {}).get(duration, 0)

    type_name = "Россия (RU)" if sub_type == "ru" else "Европа (EU)"
    duration_name = get_duration_name(duration)

    await callback.message.edit_text(
        f"🛒 <b>Подтверждение покупки</b>\n\n"
        f"📍 Тип: {type_name}\n"
        f"⏳ Срок: {duration_name}\n"
        f"💰 Стоимость: <b>{price} ₽</b>\n\n"
        f"Нажмите «Оплатить» для продолжения:",
        reply_markup=get_payment_keyboard(sub_type, duration, price),
    )
    await callback.answer()


@callback_router.callback_query(F.data.startswith("pay_"))
async def handle_payment(callback: CallbackQuery) -> None:
    """
    Handle payment - delegate to payment router.

    The payment router handles payment provider selection and processing.

    Args:
        callback: Callback query
    """
    # This is handled by payment_router
    # Keep this handler for backward compatibility
    pass


@callback_router.callback_query(F.data == "my_subscription")
async def handle_my_subscription(callback: CallbackQuery) -> None:
    """
    Handle my subscription view.

    Args:
        callback: Callback query
    """
    async for session in get_session():
        # Get user
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        service = SubscriptionService(session)
        subscription = await service.get_user_subscription(user)

        if not subscription:
            await callback.message.edit_text(
                "📱 <b>У вас нет активной подписки</b>\n\n"
                "Приобретите подписку, чтобы получить доступ к VPN.",
                reply_markup=get_start_keyboard(),
            )
        else:
            status_emoji = "✅" if subscription.is_active else "❌"
            type_emoji = "🇷🇺" if subscription.type.value == "ru" else "🇪🇺"

            traffic_info = ""
            if subscription.traffic_limit:
                used_gb = subscription.traffic_used / (1024 ** 3)
                limit_gb = subscription.traffic_limit / (1024 ** 3)
                traffic_info = (
                    f"📊 <b>Трафик:</b> {used_gb:.2f} ГБ из {limit_gb:.2f} ГБ\n"
                )

            # Build keyboard with renew button
            builder = InlineKeyboardBuilder()
            builder.button(
                text="💳 Продлить",
                callback_data=f"renew_sub_{subscription.id}"
            )
            builder.button(text="« Назад в меню", callback_data="main_menu")
            builder.adjust(1)

            await callback.message.edit_text(
                f"📱 <b>Ваша подписка</b>\n\n"
                f"{status_emoji} <b>Статус:</b> {subscription.status.value}\n"
                f"{type_emoji} <b>Тип:</b> {subscription.type.value.upper()}\n"
                f"📅 <b>Действует до:</b> {subscription.expiry_date.strftime('%d.%m.%Y')}\n"
                f"⏳ <b>Осталось дней:</b> {subscription.days_remaining}\n"
                f"{traffic_info}"
                f"\n"
                f"🔗 <b>Ссылка для подключения:</b>\n"
                f"<code>{subscription.link}</code>",
                reply_markup=builder.as_markup(),
            )

    await callback.answer()


@callback_router.callback_query(F.data == "support")
async def handle_support(callback: CallbackQuery) -> None:
    """
    Handle support button.

    Args:
        callback: Callback query
    """
    await callback.message.edit_text(
        "❓ <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, свяжитесь с нами:\n\n"
        "📧 Email: support@riovpn.example\n"
        "📱 Telegram: @riovpn_support\n\n"
        "Мы отвечаем в течение 24 часов.",
        reply_markup=get_back_keyboard(),
    )
    await callback.answer()


@callback_router.callback_query(F.data == "renew")
async def handle_renew(callback: CallbackQuery) -> None:
    """
    Handle renew button.

    Args:
        callback: Callback query
    """
    await callback.message.edit_text(
        "💳 <b>Продление подписки</b>\n\n"
        "Перейдите в раздел «Моя подписка» для продления.",
        reply_markup=get_back_keyboard(),
    )
    await callback.answer()


def get_duration_name(months: int) -> str:
    """
    Get human-readable duration name.

    Args:
        months: Number of months

    Returns:
        Duration name in Russian
    """
    if months == 1:
        return "1 месяц"
    elif months in [2, 3, 4]:
        return f"{months} месяца"
    else:
        return f"{months} месяцев"
