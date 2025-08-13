#!/usr/bin/env python3
"""
RioVPN Bot Start Handler
"""

import os
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from logger import logger

# Import configuration with fallbacks
try:
    from config import (
        CAPTCHA_ENABLE,
        CHANNEL_EXISTS,
        CHANNEL_ID,
        CHANNEL_URL,
        DONATIONS_ENABLE,
        SHOW_START_MENU_ONCE,
        SUPPORT_CHAT_URL,
        TRIAL_TIME_DISABLE,
    )
except ImportError:
    # Default values if config is not available
    CAPTCHA_ENABLE = False
    CHANNEL_EXISTS = True
    CHANNEL_ID = -1001234567890
    CHANNEL_URL = "https://t.me/your_channel"
    DONATIONS_ENABLE = True
    SHOW_START_MENU_ONCE = False
    SUPPORT_CHAT_URL = "https://t.me/your_support"
    TRIAL_TIME_DISABLE = False

# Import database functions with fallbacks
try:
    from database import (
        add_user,
        check_user_exists,
        get_coupon_by_code,
        get_key_count,
        get_trial,
    )
except ImportError:
    # Mock functions if database is not available
    async def add_user(*args, **kwargs):
        logger.info("Mock: add_user called")
    
    async def check_user_exists(*args, **kwargs):
        return False
    
    async def get_coupon_by_code(*args, **kwargs):
        return None
    
    async def get_key_count(*args, **kwargs):
        return 0
    
    async def get_trial(*args, **kwargs):
        return None

# Import handlers with fallbacks
try:
    from handlers.buttons import (
        ABOUT_VPN,
        BACK,
        CHANNEL,
        MAIN_MENU,
        SUB_CHANELL,
        SUB_CHANELL_DONE,
        SUPPORT,
        TRIAL_SUB,
    )
except ImportError:
    # Default button texts
    ABOUT_VPN = "💬 О сервисе"
    BACK = "⬅️ Назад"
    CHANNEL = "📢 Канал"
    MAIN_MENU = "👤 Личный кабинет"
    SUB_CHANELL = "📢 Подписаться"
    SUB_CHANELL_DONE = "✅ Я подписался"
    SUPPORT = "💬 Поддержка"
    TRIAL_SUB = "🎁 Пробная подписка"

try:
    from handlers.texts import (
        NOT_SUBSCRIBED_YET_MSG,
        SUBSCRIPTION_CHECK_ERROR_MSG,
        SUBSCRIPTION_CONFIRMED_MSG,
        SUBSCRIPTION_REQUIRED_MSG,
        WELCOME_TEXT,
        get_about_vpn,
    )
except ImportError:
    # Default text messages
    NOT_SUBSCRIBED_YET_MSG = "❌ Вы не подписаны на канал! Подпишитесь, чтобы продолжить."
    SUBSCRIPTION_CHECK_ERROR_MSG = "❌ Ошибка при проверке подписки. Попробуйте позже."
    SUBSCRIPTION_CONFIRMED_MSG = "✅ Подписка подтверждена! Добро пожаловать!"
    SUBSCRIPTION_REQUIRED_MSG = "📢 Для использования бота необходимо подписаться на канал."
    WELCOME_TEXT = """
🎉 Добро пожаловать в RioVPN!

🔐 Безопасный и быстрый VPN сервис
🌍 Доступ к заблокированным сайтам
⚡ Высокая скорость соединения
📱 Поддержка всех устройств

Выберите действие:
"""
    def get_about_vpn():
        return "💬 О сервисе RioVPN - современный VPN сервис"

# Import other handlers with fallbacks
try:
    from handlers.captcha import generate_captcha
except ImportError:
    async def generate_captcha(message, state):
        return {"text": "🔐 Капча временно недоступна", "markup": None}

try:
    from handlers.coupons import activate_coupon
except ImportError:
    async def activate_coupon(*args, **kwargs):
        return False

try:
    from handlers.payments.gift import handle_gift_link
except ImportError:
    async def handle_gift_link(*args, **kwargs):
        return False

try:
    from handlers.profile import process_callback_view_profile
except ImportError:
    async def process_callback_view_profile(*args, **kwargs):
        pass

try:
    from handlers.utils import edit_or_send_message
except ImportError:
    async def edit_or_send_message(target_message, text, reply_markup=None):
        await target_message.answer(text, reply_markup=reply_markup)

try:
    from handlers.refferal import handle_referral_link
except ImportError:
    async def handle_referral_link(*args, **kwargs):
        return False

router = Router()

processing_gifts = set()


@router.callback_query(F.data == "start")
async def handle_start_callback_query(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: Any,
    admin: bool,
    captcha: bool = False,
):
    await start_command(callback_query.message, state, session, admin, captcha)


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, session: Any, admin: bool, captcha: bool = True):
    logger.info(f"Вызвана функция start_command для пользователя {message.chat.id}")

    if CAPTCHA_ENABLE and captcha:
        user_exists = await check_user_exists(session, message.chat.id)
        if not user_exists:
            captcha_data = await generate_captcha(message, state)
            await edit_or_send_message(
                target_message=message,
                text=captcha_data["text"],
                reply_markup=captcha_data["markup"],
            )
            return

    state_data = await state.get_data()
    text_to_process = state_data.get("original_text", message.text)
    await process_start_logic(message, state, session, admin, text_to_process)


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback_query: CallbackQuery, state: FSMContext, session: Any, admin: bool):
    user_id = callback_query.from_user.id
    logger.info(f"[CALLBACK] Получен callback 'check_subscription' от пользователя {user_id}")

    try:
        # For now, just confirm subscription without checking
        await callback_query.answer(SUBSCRIPTION_CONFIRMED_MSG, show_alert=True)
        await process_start_logic(callback_query.message, state, session, admin, "/start")
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        await callback_query.answer(SUBSCRIPTION_CHECK_ERROR_MSG, show_alert=True)


async def process_start_logic(message: Message, state: FSMContext, session: Any, admin: bool, text: str):
    """Process the start command logic"""
    try:
        # Add user to database
        await add_user(
            session=session,
            tg_id=message.chat.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
            is_bot=message.from_user.is_bot,
        )

        # Create main menu keyboard
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=MAIN_MENU, callback_data="profile"))
        keyboard.row(InlineKeyboardButton(text=ABOUT_VPN, callback_data="about_vpn"))
        keyboard.row(InlineKeyboardButton(text=SUPPORT, url=SUPPORT_CHAT_URL))
        
        if CHANNEL_EXISTS:
            keyboard.row(InlineKeyboardButton(text=CHANNEL, url=CHANNEL_URL))

        # Send welcome message
        await message.answer(
            WELCOME_TEXT,
            reply_markup=keyboard.as_markup()
        )

    except Exception as e:
        logger.error(f"Ошибка в process_start_logic: {e}")
        await message.answer("❌ Произошла ошибка при запуске бота. Попробуйте позже.")


@router.callback_query(F.data == "about_vpn")
async def about_vpn_callback(callback_query: CallbackQuery):
    """Handle about VPN callback"""
    try:
        about_text = get_about_vpn()
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=BACK, callback_data="start"))
        
        await callback_query.message.edit_text(
            about_text,
            reply_markup=keyboard.as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка в about_vpn_callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
