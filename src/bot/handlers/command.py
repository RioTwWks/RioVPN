"""Command handlers for the bot."""

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select

from src.bot.keyboards import get_start_keyboard
from src.bot.handlers.referral import process_referral_start
from src.core.database import get_session
from src.models.user import User
from src.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)

command_router = Router()


@command_router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """
    Handle /start command.

    Args:
        message: Incoming message
    """
    async for session in get_session():
        # Get or create user
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"New user registered: {message.from_user.id}")

        # Check for referral parameter
        if message.text and len(message.text.split()) > 1:
            start_param = message.text.split()[1]
            referred = await process_referral_start(message, start_param)
            if referred:
                await message.answer(
                    "🎉 <b>Добро пожаловать!</b>\n\n"
                    "Вы присоединились по реферальной ссылке.\n"
                    "При первой оплате ваш друг получит бонус, а вы скидку 10%!"
                )
                return

        await message.answer(
            f"👋 <b>Добро пожаловать в RioVPN!</b>\n\n"
            f"Я помогу вам приобрести надежную VPN-подписку.\n\n"
            f"🔹 <b>Россия (RU)</b> - обход белых списков мобильных операторов\n"
            f"🔹 <b>Европа (EU)</b> - выход в мировой интернет\n\n"
            f"Выберите действие в меню:",
            reply_markup=get_start_keyboard(),
        )


@command_router.message(Command("buy"))
async def handle_buy(message: Message) -> None:
    """
    Handle /buy command.

    Args:
        message: Incoming message
    """
    await message.answer(
        "🛒 <b>Покупка подписки</b>\n\n"
        "Выберите тип подписки в меню ниже:",
        reply_markup=get_start_keyboard(),
    )


@command_router.message(Command("my"))
async def handle_my(message: Message) -> None:
    """
    Handle /my command - show user's subscription.

    Args:
        message: Incoming message
    """
    async for session in get_session():
        # Get user
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден. Нажмите /start")
            return

        service = SubscriptionService(session)
        subscription = await service.get_user_subscription(user)

        if not subscription:
            await message.answer(
                "📱 <b>У вас нет активной подписки</b>\n\n"
                "Приобретите подписку, чтобы получить доступ к VPN.",
                reply_markup=get_start_keyboard(),
            )
            return

        # Format subscription info
        status_emoji = "✅" if subscription.is_active else "❌"
        type_emoji = "🇷🇺" if subscription.type.value == "ru" else "🇪🇺"

        traffic_info = ""
        if subscription.traffic_limit:
            used_gb = subscription.traffic_used / (1024 ** 3)
            limit_gb = subscription.traffic_limit / (1024 ** 3)
            traffic_info = (
                f"📊 <b>Трафик:</b> {used_gb:.2f} ГБ из {limit_gb:.2f} ГБ\n"
                f"     Использовано: {subscription.traffic_used_percent:.1f}%\n"
            )

        await message.answer(
            f"📱 <b>Ваша подписка</b>\n\n"
            f"{status_emoji} <b>Статус:</b> {subscription.status.value}\n"
            f"{type_emoji} <b>Тип:</b> {subscription.type.value.upper()}\n"
            f"📅 <b>Действует до:</b> {subscription.expiry_date.strftime('%d.%m.%Y')}\n"
            f"⏳ <b>Осталось дней:</b> {subscription.days_remaining}\n"
            f"{traffic_info}"
            f"\n"
            f"Для подключения используйте ссылку, которую я отправил ранее.",
            reply_markup=get_start_keyboard(),
        )


@command_router.message(Command("support"))
async def handle_support(message: Message) -> None:
    """
    Handle /support command.

    Args:
        message: Incoming message
    """
    await message.answer(
        "❓ <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, свяжитесь с нами:\n\n"
        "📧 Email: support@riovpn.example\n"
        "📱 Telegram: @riovpn_support\n\n"
        "Мы отвечаем в течение 24 часов.",
        reply_markup=get_start_keyboard(),
    )


@command_router.message(Command("renew"))
async def handle_renew(message: Message) -> None:
    """
    Handle /renew command.

    Args:
        message: Incoming message
    """
    await message.answer(
        "💳 <b>Продление подписки</b>\n\n"
        "Перейдите в раздел «Моя подписка» для продления.",
        reply_markup=get_start_keyboard(),
    )
