#!/usr/bin/env python3
"""
RioVPN Bot Payment Handler
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
        CUSTOM_AMOUNT,
        PAY,
        PAY_2,
    )
except ImportError:
    # Default button texts
    BACK = "⬅️ Назад"
    CUSTOM_AMOUNT = "💰 Ввести свою сумму"
    PAY = "Пополнить"
    PAY_2 = "Оплатить"

# Import texts with fallbacks
try:
    from handlers.texts import BALANCE_MANAGEMENT_TEXT, PAYMENT_METHODS_MSG
except ImportError:
    # Default text messages
    def BALANCE_MANAGEMENT_TEXT(balance):
        return f"""
💵 Управление балансом

Ваш текущий баланс: {balance} ₽

Выберите действие:
"""
    
    PAYMENT_METHODS_MSG = """
💳 Выберите способ оплаты:

💳 ЮКасса - быстрая оплата картой
💳 ЮMoney - перевод по номеру телефона
💰 FreeKassa - международные платежи
💰 CryptoBot - криптовалюта
⭐ RoboKassa - популярная касса
"""

# Import database functions with fallbacks
try:
    from database import get_balance
except ImportError:
    # Mock functions if database is not available
    async def get_balance(*args, **kwargs):
        return 0.0

router = Router()


@router.callback_query(F.data == "pay")
async def pay_callback(callback_query: CallbackQuery, session: Any):
    """Handle payment callback"""
    try:
        user_id = callback_query.from_user.id
        balance = await get_balance(session, user_id)
        
        balance_text = BALANCE_MANAGEMENT_TEXT(balance)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="💳 ЮКасса", callback_data="pay_yookassa"))
        keyboard.row(InlineKeyboardButton(text="💳 ЮMoney", callback_data="pay_yoomoney"))
        keyboard.row(InlineKeyboardButton(text="💰 CryptoBot", callback_data="pay_cryptobot"))
        keyboard.row(InlineKeyboardButton(text="⭐ RoboKassa", callback_data="pay_robokassa"))
        keyboard.row(InlineKeyboardButton(text=CUSTOM_AMOUNT, callback_data="pay_custom"))
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="balance"))
        
        await callback_query.message.edit_text(
            balance_text + PAYMENT_METHODS_MSG,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в pay_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "pay_yookassa")
async def pay_yookassa_callback(callback_query: CallbackQuery):
    """Handle YooKassa payment callback"""
    try:
        payment_text = """
💳 <b>Оплата через ЮКасса</b>

Функция оплаты временно недоступна

В будущем здесь можно будет:
• Выбрать сумму для пополнения
• Перейти к оплате через ЮКасса
• Получить уведомление об успешной оплате
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="pay"))
        
        await callback_query.message.edit_text(
            payment_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в pay_yookassa_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "pay_yoomoney")
async def pay_yoomoney_callback(callback_query: CallbackQuery):
    """Handle YooMoney payment callback"""
    try:
        payment_text = """
💳 <b>Оплата через ЮMoney</b>

Функция оплаты временно недоступна

В будущем здесь можно будет:
• Выбрать сумму для пополнения
• Перейти к оплате через ЮMoney
• Получить уведомление об успешной оплате
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="pay"))
        
        await callback_query.message.edit_text(
            payment_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в pay_yoomoney_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "pay_cryptobot")
async def pay_cryptobot_callback(callback_query: CallbackQuery):
    """Handle CryptoBot payment callback"""
    try:
        payment_text = """
💰 <b>Оплата через CryptoBot</b>

Функция оплаты временно недоступна

В будущем здесь можно будет:
• Выбрать сумму для пополнения
• Перейти к оплате через CryptoBot
• Получить уведомление об успешной оплате
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="pay"))
        
        await callback_query.message.edit_text(
            payment_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в pay_cryptobot_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "pay_robokassa")
async def pay_robokassa_callback(callback_query: CallbackQuery):
    """Handle RoboKassa payment callback"""
    try:
        payment_text = """
⭐ <b>Оплата через RoboKassa</b>

Функция оплаты временно недоступна

В будущем здесь можно будет:
• Выбрать сумму для пополнения
• Перейти к оплате через RoboKassa
• Получить уведомление об успешной оплате
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="pay"))
        
        await callback_query.message.edit_text(
            payment_text,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в pay_robokassa_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "pay_custom")
async def pay_custom_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle custom amount payment callback"""
    try:
        payment_text = """
💰 <b>Введите сумму для пополнения</b>

Минимальная сумма: 10 ₽
Максимальная сумма: 15,000 ₽

Отправьте сумму числом (например: 100)
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="pay"))
        
        await callback_query.message.edit_text(
            payment_text,
            reply_markup=keyboard.as_markup()
        )
        
        # Set state to wait for amount
        await state.set_state("waiting_for_amount")
        
    except Exception as e:
        logger.error(f"Ошибка в pay_custom_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.message(F.text.regexp(r"^\d+$"))
async def handle_amount_input(message: Message, state: FSMContext):
    """Handle amount input from user"""
    try:
        current_state = await state.get_state()
        if current_state != "waiting_for_amount":
            return
        
        amount = int(message.text)
        
        if amount < 10:
            await message.answer("❌ Минимальная сумма пополнения: 10 ₽")
            return
        
        if amount > 15000:
            await message.answer("❌ Максимальная сумма пополнения: 15,000 ₽")
            return
        
        payment_text = f"""
💰 <b>Подтверждение оплаты</b>

Сумма: {amount} ₽

Выберите способ оплаты:
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="💳 ЮКасса", callback_data=f"pay_yookassa_{amount}"))
        keyboard.row(InlineKeyboardButton(text="💳 ЮMoney", callback_data=f"pay_yoomoney_{amount}"))
        keyboard.row(InlineKeyboardButton(text="💰 CryptoBot", callback_data=f"pay_cryptobot_{amount}"))
        keyboard.row(InlineKeyboardButton(text="⭐ RoboKassa", callback_data=f"pay_robokassa_{amount}"))
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="pay"))
        
        await message.answer(
            payment_text,
            reply_markup=keyboard.as_markup()
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в handle_amount_input: {e}")
        await message.answer("❌ Произошла ошибка при обработке суммы")
        await state.clear()
