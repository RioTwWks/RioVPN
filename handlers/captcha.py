#!/usr/bin/env python3
"""
RioVPN Bot Captcha Handler
"""

import random
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from logger import logger

# Import texts with fallbacks
try:
    from handlers.texts import CAPTCHA_EMOJIS, CAPTCHA_PROMPT_MSG
except ImportError:
    # Default captcha texts
    CAPTCHA_EMOJIS = ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇"]
    CAPTCHA_PROMPT_MSG = "🔐 Для продолжения решите капчу:"

router = Router()


async def generate_captcha(message: Message, state: FSMContext) -> dict:
    """Generate a simple captcha"""
    try:
        # Generate random emojis
        emojis = random.sample(CAPTCHA_EMOJIS, 6)
        target_emoji = random.choice(emojis)
        
        # Create keyboard with emojis
        keyboard = InlineKeyboardBuilder()
        
        # Arrange emojis in 2x3 grid
        for i in range(0, 6, 3):
            row = []
            for j in range(3):
                if i + j < len(emojis):
                    emoji = emojis[i + j]
                    callback_data = f"captcha_{emoji}_{emoji == target_emoji}"
                    row.append(InlineKeyboardButton(text=emoji, callback_data=callback_data))
            keyboard.row(*row)
        
        # Store correct answer in state
        await state.update_data(captcha_answer=target_emoji)
        
        captcha_text = f"{CAPTCHA_PROMPT_MSG}\n\nНажмите на: {target_emoji}"
        
        return {
            "text": captcha_text,
            "markup": keyboard.as_markup()
        }
        
    except Exception as e:
        logger.error(f"Ошибка при генерации капчи: {e}")
        return {
            "text": "🔐 Капча временно недоступна. Попробуйте позже.",
            "markup": None
        }


@router.callback_query(F.data.startswith("captcha_"))
async def handle_captcha_answer(callback_query: CallbackQuery, state: FSMContext):
    """Handle captcha answer"""
    try:
        # Parse callback data
        parts = callback_query.data.split("_")
        if len(parts) != 3:
            await callback_query.answer("❌ Неверный формат капчи", show_alert=True)
            return
        
        selected_emoji = parts[1]
        is_correct = parts[2] == "True"
        
        # Get correct answer from state
        state_data = await state.get_data()
        correct_answer = state_data.get("captcha_answer")
        
        if not correct_answer:
            await callback_query.answer("❌ Капча устарела. Попробуйте /start", show_alert=True)
            return
        
        if is_correct:
            # Correct answer
            await callback_query.answer("✅ Капча решена!", show_alert=True)
            
            # Clear captcha state
            await state.clear()
            
            # Send success message and redirect to start
            await callback_query.message.edit_text(
                "✅ Капча решена! Добро пожаловать в RioVPN!\n\nИспользуйте /start для начала работы."
            )
            
        else:
            # Wrong answer
            await callback_query.answer("❌ Неверный ответ. Попробуйте еще раз.", show_alert=True)
            
            # Generate new captcha
            captcha_data = await generate_captcha(callback_query.message, state)
            await callback_query.message.edit_text(
                captcha_data["text"],
                reply_markup=captcha_data["markup"]
            )
            
    except Exception as e:
        logger.error(f"Ошибка при обработке капчи: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)


@router.message(F.text == "/captcha")
async def captcha_command(message: Message, state: FSMContext):
    """Handle /captcha command"""
    try:
        captcha_data = await generate_captcha(message, state)
        await message.answer(
            captcha_data["text"],
            reply_markup=captcha_data["markup"]
        )
    except Exception as e:
        logger.error(f"Ошибка в captcha_command: {e}")
        await message.answer("❌ Произошла ошибка при генерации капчи")
