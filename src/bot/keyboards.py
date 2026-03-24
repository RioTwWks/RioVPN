"""Inline keyboards for the bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_keyboard() -> InlineKeyboardMarkup:
    """
    Get main menu keyboard.

    Returns:
        InlineKeyboardMarkup with main menu options
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Купить подписку", callback_data="buy")
    builder.button(text="📱 Моя подписка", callback_data="my_subscription")
    builder.button(text="🎁 Рефералы", callback_data="referral")
    builder.button(text="💳 Продлить", callback_data="renew")
    builder.button(text="❓ Поддержка", callback_data="support")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_subscription_type_keyboard() -> InlineKeyboardMarkup:
    """
    Get subscription type selection keyboard.

    Returns:
        InlineKeyboardMarkup with RU/EU options
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🇷🇺 Россия (обход белых списков)",
        callback_data="sub_type_ru"
    )
    builder.button(
        text="🇪🇺 Европа (выход в мировой интернет)",
        callback_data="sub_type_eu"
    )
    builder.button(text="« Назад", callback_data="main_menu")
    builder.adjust(1, 1)
    return builder.as_markup()


def get_subscription_duration_keyboard(sub_type: str) -> InlineKeyboardMarkup:
    """
    Get subscription duration selection keyboard.

    Args:
        sub_type: Subscription type (ru/eu)

    Returns:
        InlineKeyboardMarkup with duration options
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="1 месяц", callback_data=f"duration_{sub_type}_1")
    builder.button(text="3 месяца", callback_data=f"duration_{sub_type}_3")
    builder.button(text="6 месяцев", callback_data=f"duration_{sub_type}_6")
    builder.button(text="12 месяцев", callback_data=f"duration_{sub_type}_12")
    builder.button(text="« Назад", callback_data="select_type")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_payment_keyboard(sub_type: str, duration: int, price: float) -> InlineKeyboardMarkup:
    """
    Get payment confirmation keyboard.

    Args:
        sub_type: Subscription type
        duration: Duration in months
        price: Price in RUB

    Returns:
        InlineKeyboardMarkup with payment options
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💰 Оплатить {price} ₽",
        callback_data=f"pay_{sub_type}_{duration}"
    )
    builder.button(text="« Назад", callback_data="select_type")
    builder.adjust(1)
    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """
    Get back button keyboard.

    Returns:
        InlineKeyboardMarkup with back button
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="« Назад в меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """
    Get admin panel keyboard.

    Returns:
        InlineKeyboardMarkup with admin options
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="👥 Пользователи", callback_data="admin_users")
    builder.button(text="💰 Платежи", callback_data="admin_payments")
    builder.button(text="💬 Рассылка", callback_data="admin_broadcast")
    builder.adjust(2, 2)
    return builder.as_markup()


def get_subscription_info_keyboard(subscription_id: int) -> InlineKeyboardMarkup:
    """
    Get subscription info keyboard with renew option.

    Args:
        subscription_id: Subscription ID

    Returns:
        InlineKeyboardMarkup with renew option
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 Продлить",
        callback_data=f"renew_sub_{subscription_id}"
    )
    builder.button(text="« Назад в меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
