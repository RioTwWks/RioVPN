#!/usr/bin/env python3
"""
RioVPN Bot Profile Handler
"""

from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from logger import logger

# Import handlers with fallbacks
try:
    from handlers.buttons import (
        ADD_SUB,
        BACK,
        BALANCE,
        GIFTS,
        INVITE,
        MAIN_MENU,
        MY_SUBS,
        RENEW_SUB,
    )
except ImportError:
    # Default button texts
    ADD_SUB = "➕ Добавить новую подписку"
    BACK = "⬅️ Назад"
    BALANCE = "💵 Баланс"
    GIFTS = "🎁 Подарить"
    INVITE = "👥 Пригласить"
    MAIN_MENU = "👤 Личный кабинет"
    MY_SUBS = "📱 Мои подписки"
    RENEW_SUB = "🔄 Обновить подписку"

# Import database functions with fallbacks
try:
    from database import get_balance, get_key_count
except ImportError:
    # Mock functions if database is not available
    async def get_balance(*args, **kwargs):
        return 0.0
    
    async def get_key_count(*args, **kwargs):
        return 0

router = Router()


@router.callback_query(F.data == "profile")
async def process_callback_view_profile(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: Any,
    admin: bool,
):
    """Handle profile view callback"""
    try:
        user_id = callback_query.from_user.id
        logger.info(f"Пользователь {user_id} открыл профиль")

        # Get user data
        balance = await get_balance(session, user_id)
        key_count = await get_key_count(session, user_id)

        # Create profile text
        profile_text = f"""
👤 <b>Личный кабинет</b>

🆔 ID: <code>{user_id}</code>
👤 Имя: {callback_query.from_user.first_name or 'Не указано'}
💵 Баланс: {balance} ₽
📱 Подписок: {key_count}

Выберите действие:
"""

        # Create keyboard
        keyboard = InlineKeyboardBuilder()
        
        if key_count == 0:
            keyboard.row(InlineKeyboardButton(text=ADD_SUB, callback_data="create_key"))
        else:
            keyboard.row(InlineKeyboardButton(text=MY_SUBS, callback_data="my_keys"))
            keyboard.row(InlineKeyboardButton(text=RENEW_SUB, callback_data="renew_key"))
        
        keyboard.row(InlineKeyboardButton(text=BALANCE, callback_data="balance"))
        keyboard.row(InlineKeyboardButton(text=INVITE, callback_data="referral"))
        keyboard.row(InlineKeyboardButton(text=GIFTS, callback_data="gifts"))
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="start"))

        # Send profile
        await callback_query.message.edit_text(
            profile_text,
            reply_markup=keyboard.as_markup()
        )

    except Exception as e:
        logger.error(f"Ошибка в process_callback_view_profile: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "balance")
async def balance_callback(callback_query: CallbackQuery, session: Any):
    """Handle balance callback"""
    try:
        user_id = callback_query.from_user.id
        balance = await get_balance(session, user_id)
        
        balance_text = f"""
💵 <b>Управление балансом</b>

Ваш текущий баланс: <b>{balance} ₽</b>

Выберите действие:
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="💳 Пополнить", callback_data="pay"))
        keyboard.row(InlineKeyboardButton(text="📊 История", callback_data="balance_history"))
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="profile"))
        
        await callback_query.message.edit_text(
            balance_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в balance_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "my_keys")
async def my_keys_callback(callback_query: CallbackQuery, session: Any):
    """Handle my keys callback"""
    try:
        user_id = callback_query.from_user.id
        key_count = await get_key_count(session, user_id)
        
        if key_count == 0:
            text = "📱 У вас пока нет активных подписок"
            keyboard = InlineKeyboardBuilder()
            keyboard.row(InlineKeyboardButton(text=ADD_SUB, callback_data="create_key"))
        else:
            text = f"📱 У вас {key_count} активных подписок\n\nФункция просмотра подписок временно недоступна"
            keyboard = InlineKeyboardBuilder()
        
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="profile"))
        
        await callback_query.message.edit_text(
            text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в my_keys_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "referral")
async def referral_callback(callback_query: CallbackQuery):
    """Handle referral callback"""
    try:
        user_id = callback_query.from_user.id
        
        referral_text = f"""
👥 <b>Реферальная программа</b>

Приглашайте друзей и получайте бонусы!

🔗 Ваша реферальная ссылка:
https://t.me/your_bot?start=referral_{user_id}

💰 Бонус за приглашение: 10 ₽
📊 Приглашено пользователей: 0

Функция рефералов временно недоступна
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="profile"))
        
        await callback_query.message.edit_text(
            referral_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в referral_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "gifts")
async def gifts_callback(callback_query: CallbackQuery):
    """Handle gifts callback"""
    try:
        gifts_text = """
🎁 <b>Подарки</b>

Функция подарков временно недоступна

В будущем здесь можно будет:
• Отправлять подарки друзьям
• Получать подарки от друзей
• Просматривать историю подарков
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="profile"))
        
        await callback_query.message.edit_text(
            gifts_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в gifts_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
