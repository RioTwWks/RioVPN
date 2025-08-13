#!/usr/bin/env python3
"""
RioVPN Bot Referral Handler
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
        BACK,
        INVITE,
    )
except ImportError:
    # Default button texts
    BACK = "⬅️ Назад"
    INVITE = "👥 Пригласить"

# Import texts with fallbacks
try:
    from handlers.texts import REFERRAL_WELCOME_MSG
except ImportError:
    # Default referral text
    def REFERRAL_WELCOME_MSG(referral_link, bonus, count):
        return f"""
👥 <b>Реферальная программа</b>

Приглашайте друзей и получайте бонусы!

🔗 Ваша реферальная ссылка:
{referral_link}

💰 Бонус за приглашение: {bonus} ₽
📊 Приглашено пользователей: {count}
"""

# Import database functions with fallbacks
try:
    from database import get_referral_stats, create_referral
except ImportError:
    # Mock functions if database is not available
    async def get_referral_stats(*args, **kwargs):
        return {"count": 0, "bonus": 10}
    
    async def create_referral(*args, **kwargs):
        return False

router = Router()


@router.callback_query(F.data == "referral")
async def referral_callback(callback_query: CallbackQuery, session: Any):
    """Handle referral callback"""
    try:
        user_id = callback_query.from_user.id
        
        # Get referral stats
        stats = await get_referral_stats(session, user_id)
        referral_count = stats.get("count", 0)
        bonus_amount = stats.get("bonus", 10)
        
        # Generate referral link
        bot_username = "your_bot"  # This should come from config
        referral_link = f"https://t.me/{bot_username}?start=referral_{user_id}"
        
        referral_text = REFERRAL_WELCOME_MSG(referral_link, bonus_amount, referral_count)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="copy_referral_link"))
        keyboard.row(InlineKeyboardButton(text="📊 Статистика", callback_data="referral_stats"))
        keyboard.row(InlineKeyboardButton(text="💰 Вывести бонусы", callback_data="withdraw_referral_bonus"))
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="profile"))
        
        await callback_query.message.edit_text(
            referral_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в referral_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "copy_referral_link")
async def copy_referral_link_callback(callback_query: CallbackQuery, session: Any):
    """Handle copy referral link callback"""
    try:
        user_id = callback_query.from_user.id
        bot_username = "your_bot"  # This should come from config
        referral_link = f"https://t.me/{bot_username}?start=referral_{user_id}"
        
        await callback_query.answer(
            f"🔗 Ссылка скопирована: {referral_link}",
            show_alert=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка в copy_referral_link_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "referral_stats")
async def referral_stats_callback(callback_query: CallbackQuery, session: Any):
    """Handle referral stats callback"""
    try:
        user_id = callback_query.from_user.id
        
        # Get referral stats
        stats = await get_referral_stats(session, user_id)
        referral_count = stats.get("count", 0)
        bonus_amount = stats.get("bonus", 10)
        total_earned = referral_count * bonus_amount
        
        stats_text = f"""
📊 <b>Статистика рефералов</b>

👥 Приглашено пользователей: {referral_count}
💰 Бонус за приглашение: {bonus_amount} ₽
💵 Всего заработано: {total_earned} ₽

Функция детальной статистики временно недоступна
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="referral"))
        
        await callback_query.message.edit_text(
            stats_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в referral_stats_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "withdraw_referral_bonus")
async def withdraw_referral_bonus_callback(callback_query: CallbackQuery, session: Any):
    """Handle withdraw referral bonus callback"""
    try:
        user_id = callback_query.from_user.id
        
        # Get referral stats
        stats = await get_referral_stats(session, user_id)
        referral_count = stats.get("count", 0)
        bonus_amount = stats.get("bonus", 10)
        total_earned = referral_count * bonus_amount
        
        if total_earned <= 0:
            await callback_query.answer(
                "❌ У вас нет бонусов для вывода",
                show_alert=True
            )
            return
        
        withdraw_text = f"""
💰 <b>Вывод реферальных бонусов</b>

Доступно для вывода: {total_earned} ₽

Функция вывода бонусов временно недоступна

В будущем здесь можно будет:
• Вывести бонусы на баланс
• Получить уведомление об успешном выводе
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="referral"))
        
        await callback_query.message.edit_text(
            withdraw_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в withdraw_referral_bonus_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


async def handle_referral_link(referrer_id: int, message: Message, state: FSMContext, session: Any, user_data: dict = None):
    """Handle referral link processing"""
    try:
        user_id = message.from_user.id
        
        # Don't allow self-referral
        if referrer_id == user_id:
            logger.warning(f"Пользователь {user_id} попытался пригласить сам себя")
            return False
        
        # Create referral
        success = await create_referral(session, referrer_id, user_id)
        
        if success:
            logger.info(f"Создана реферальная связь: {referrer_id} -> {user_id}")
            return True
        else:
            logger.warning(f"Не удалось создать реферальную связь: {referrer_id} -> {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при обработке реферальной ссылки: {e}")
        return False


@router.message(F.text == "/referral")
async def referral_command(message: Message, session: Any):
    """Handle /referral command"""
    try:
        await referral_callback(
            type('MockCallback', (), {
                'message': message,
                'answer': lambda text, **kwargs: None,
                'from_user': message.from_user
            })()
        )
    except Exception as e:
        logger.error(f"Ошибка в referral_command: {e}")
        await message.answer("❌ Произошла ошибка при обработке команды рефералов")
