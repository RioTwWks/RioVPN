#!/usr/bin/env python3
"""
RioVPN Bot Donation Handler
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
        DONATE,
    )
except ImportError:
    # Default button texts
    BACK = "⬅️ Назад"
    DONATE = "💰 Поддержать проект"

router = Router()


@router.callback_query(F.data == "donate")
async def donate_callback(callback_query: CallbackQuery):
    """Handle donation callback"""
    try:
        donate_text = """
💰 <b>Поддержать проект RioVPN</b>

Спасибо за желание поддержать наш проект!

Ваша поддержка помогает нам:
• Развивать сервис
• Добавлять новые серверы
• Улучшать безопасность
• Поддерживать стабильную работу

Выберите способ поддержки:
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="💳 Банковская карта", callback_data="donate_card"))
        keyboard.row(InlineKeyboardButton(text="💰 Криптовалюта", callback_data="donate_crypto"))
        keyboard.row(InlineKeyboardButton(text="💳 ЮMoney", callback_data="donate_yoomoney"))
        keyboard.row(InlineKeyboardButton(text="💳 ЮКасса", callback_data="donate_yookassa"))
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="about_vpn"))
        
        await callback_query.message.edit_text(
            donate_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в donate_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "donate_card")
async def donate_card_callback(callback_query: CallbackQuery):
    """Handle card donation callback"""
    try:
        donate_text = """
💳 <b>Поддержка банковской картой</b>

Функция донатов временно недоступна

В будущем здесь можно будет:
• Выбрать сумму доната
• Перейти к оплате картой
• Получить благодарность
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="donate"))
        
        await callback_query.message.edit_text(
            donate_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в donate_card_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "donate_crypto")
async def donate_crypto_callback(callback_query: CallbackQuery):
    """Handle crypto donation callback"""
    try:
        donate_text = """
💰 <b>Поддержка криптовалютой</b>

Функция донатов временно недоступна

В будущем здесь можно будет:
• Выбрать криптовалюту
• Получить адрес кошелька
• Отправить донат
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="donate"))
        
        await callback_query.message.edit_text(
            donate_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в donate_crypto_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "donate_yoomoney")
async def donate_yoomoney_callback(callback_query: CallbackQuery):
    """Handle YooMoney donation callback"""
    try:
        donate_text = """
💳 <b>Поддержка через ЮMoney</b>

Функция донатов временно недоступна

В будущем здесь можно будет:
• Выбрать сумму доната
• Перейти к оплате через ЮMoney
• Получить благодарность
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="donate"))
        
        await callback_query.message.edit_text(
            donate_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в donate_yoomoney_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "donate_yookassa")
async def donate_yookassa_callback(callback_query: CallbackQuery):
    """Handle YooKassa donation callback"""
    try:
        donate_text = """
💳 <b>Поддержка через ЮКасса</b>

Функция донатов временно недоступна

В будущем здесь можно будет:
• Выбрать сумму доната
• Перейти к оплате через ЮКасса
• Получить благодарность
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="donate"))
        
        await callback_query.message.edit_text(
            donate_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в donate_yookassa_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.message(F.text == "/donate")
async def donate_command(message: Message):
    """Handle /donate command"""
    try:
        await donate_callback(
            type('MockCallback', (), {
                'message': message,
                'answer': lambda text, **kwargs: None
            })()
        )
    except Exception as e:
        logger.error(f"Ошибка в donate_command: {e}")
        await message.answer("❌ Произошла ошибка при обработке команды доната")
