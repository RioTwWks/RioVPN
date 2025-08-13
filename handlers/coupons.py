#!/usr/bin/env python3
"""
RioVPN Bot Coupons Handler
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
        COUPON,
        COUPON_RESTART,
    )
except ImportError:
    # Default button texts
    BACK = "⬅️ Назад"
    COUPON = "🎟️ Активировать купон"
    COUPON_RESTART = "🎟️ Попробовать другой купон"

# Import database functions with fallbacks
try:
    from database import get_coupon_by_code, activate_coupon_for_user
except ImportError:
    # Mock functions if database is not available
    async def get_coupon_by_code(*args, **kwargs):
        return None
    
    async def activate_coupon_for_user(*args, **kwargs):
        return False

router = Router()


@router.callback_query(F.data == "activate_coupon")
async def activate_coupon_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle activate coupon callback"""
    try:
        coupon_text = """
🎟️ <b>Активация купона</b>

Введите код купона для получения скидки или бонуса.

Отправьте код купона (например: WELCOME2024)
"""
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="balance"))
        
        await callback_query.message.edit_text(
            coupon_text,
            reply_markup=keyboard.as_markup()
        )
        
        # Set state to wait for coupon code
        await state.set_state("waiting_for_coupon")
        
    except Exception as e:
        logger.error(f"Ошибка в activate_coupon_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.message(F.text.regexp(r"^[A-Z0-9]{4,20}$"))
async def handle_coupon_input(message: Message, state: FSMContext, session: Any):
    """Handle coupon code input"""
    try:
        current_state = await state.get_state()
        if current_state != "waiting_for_coupon":
            return
        
        coupon_code = message.text.upper()
        user_id = message.from_user.id
        
        # Check if coupon exists
        coupon = await get_coupon_by_code(session, coupon_code)
        
        if not coupon:
            await message.answer(
                "❌ Купон не найден или недействителен.\n\n"
                "Проверьте правильность кода и попробуйте снова.",
                reply_markup=InlineKeyboardBuilder().row(
                    InlineKeyboardButton(text=COUPON_RESTART, callback_data="activate_coupon")
                ).as_markup()
            )
            await state.clear()
            return
        
        # Try to activate coupon
        success = await activate_coupon_for_user(session, user_id, coupon_code)
        
        if success:
            await message.answer(
                f"✅ Купон <code>{coupon_code}</code> успешно активирован!\n\n"
                f"🎉 Вы получили скидку {coupon.discount_percent}% на следующую покупку.",
                reply_markup=InlineKeyboardBuilder().row(
                    InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="pay")
                ).as_markup()
            )
        else:
            await message.answer(
                "❌ Не удалось активировать купон.\n\n"
                "Возможные причины:\n"
                "• Купон уже использован\n"
                "• Купон истек\n"
                "• Достигнут лимит использований",
                reply_markup=InlineKeyboardBuilder().row(
                    InlineKeyboardButton(text=COUPON_RESTART, callback_data="activate_coupon")
                ).as_markup()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в handle_coupon_input: {e}")
        await message.answer("❌ Произошла ошибка при активации купона")
        await state.clear()


@router.message(F.text == "/coupon")
async def coupon_command(message: Message, state: FSMContext):
    """Handle /coupon command"""
    try:
        await activate_coupon_callback(
            type('MockCallback', (), {
                'message': message,
                'answer': lambda text, **kwargs: None
            })(),
            state
        )
    except Exception as e:
        logger.error(f"Ошибка в coupon_command: {e}")
        await message.answer("❌ Произошла ошибка при обработке команды купона")
