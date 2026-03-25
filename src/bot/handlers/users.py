"""Admin user management handlers."""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from src.bot.keyboards import get_admin_back_keyboard
from src.core.database import get_session
from src.core.logging import get_logger
from src.models.subscription import Subscription, SubscriptionStatus
from src.models.user import User

logger = get_logger(__name__)

user_router = Router()


@user_router.callback_query(F.data == "admin_users")
async def handle_admin_users(callback: CallbackQuery) -> None:
    """
    Handle admin users list command.

    Args:
        callback: Callback query
    """
    async for session in get_session():
        result = await session.execute(select(User).order_by(User.created_at.desc()).limit(20))
        users = result.scalars().all()

        text = "👥 <b>Пользователи (последние 20)</b>\n\n"

        for user in users:
            # Count subscriptions
            sub_result = await session.execute(select(Subscription).where(Subscription.user_id == user.id))
            subs = sub_result.scalars().all()
            active_subs = sum(1 for s in subs if s.status == SubscriptionStatus.active)

            username = f"@{user.username}" if user.username else "N/A"
            text += (
                f"🆔 <code>{user.telegram_id}</code>\n"
                f"👤 {username}\n"
                f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n"
                f"📱 Подписок: {len(subs)} (активных: {active_subs})\n\n"
            )

        await callback.message.edit_text(
            text,
            reply_markup=get_admin_back_keyboard(),
        )

    await callback.answer()


@user_router.message(Command("users"))
async def handle_users_command(message: Message) -> None:
    """
    Handle /users command - list all users.

    Usage: /users [limit]

    Args:
        message: Incoming message
    """
    args = message.text.split()
    limit = int(args[1]) if len(args) > 1 else 20

    async for session in get_session():
        result = await session.execute(select(User).order_by(User.created_at.desc()).limit(limit))
        users = result.scalars().all()

        text = f"👥 <b>Пользователи (последние {limit})</b>\n\n"

        for user in users:
            username = f"@{user.username}" if user.username else "N/A"
            text += f"🆔 <code>{user.telegram_id}</code> | {username} | {user.created_at.strftime('%d.%m.%Y')}\n"

        await message.answer(text)


@user_router.message(Command("search"))
async def handle_search_command(message: Message) -> None:
    """
    Handle /search command - search user by telegram_id.

    Usage: /search <telegram_id>

    Args:
        message: Incoming message
    """
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /search <telegram_id>")
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат Telegram ID")
        return

    async for session in get_session():
        # Find user
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(f"❌ Пользователь {telegram_id} не найден")
            return

        # Get subscriptions
        sub_result = await session.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscriptions = sub_result.scalars().all()

        # Format user info
        username = f"@{user.username}" if user.username else "N/A"
        text = (
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"🆔 <b>ID:</b> <code>{user.telegram_id}</code>\n"
            f"👤 <b>Username:</b> {username}\n"
            f"📅 <b>Регистрация:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📱 <b>Подписки ({len(subscriptions)})</b>\n"
        )

        for sub in subscriptions:
            status_emoji = "✅" if sub.status == SubscriptionStatus.active else "❌"
            type_emoji = "🇷🇺" if sub.type.value == "ru" else "🇪🇺"

            text += (
                f"\n{status_emoji} <b>ID:</b> {sub.id}\n"
                f"{type_emoji} <b>Тип:</b> {sub.type.value.upper()}\n"
                f"📊 <b>Статус:</b> {sub.status.value}\n"
                f"📅 <b>Действует до:</b> {sub.expiry_date.strftime('%d.%m.%Y')}\n"
            )

            if sub.traffic_limit:
                used_gb = sub.traffic_used / (1024**3)
                limit_gb = sub.traffic_limit / (1024**3)
                text += f"💾 <b>Трафик:</b> {used_gb:.2f} ГБ / {limit_gb:.2f} ГБ\n"

        await message.answer(text)


@user_router.message(Command("userhistory"))
async def handle_user_history_command(message: Message) -> None:
    """
    Handle /userhistory command - show user's payment and subscription history.

    Usage: /userhistory <telegram_id>

    Args:
        message: Incoming message
    """
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /userhistory <telegram_id>")
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат Telegram ID")
        return

    async for session in get_session():
        # Find user
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(f"❌ Пользователь {telegram_id} не найден")
            return

        # Get all subscriptions (including historical)
        sub_result = await session.execute(
            select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc())
        )
        subscriptions = sub_result.scalars().all()

        # Get all payments
        from src.models.payment import Payment

        payment_result = await session.execute(
            select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc())
        )
        payments = payment_result.scalars().all()

        text = f"📜 <b>История пользователя {telegram_id}</b>\n\n"

        # Subscriptions
        text += f"📱 <b>Подписки ({len(subscriptions)})</b>\n"
        for sub in subscriptions[:10]:  # Last 10
            text += f"  • {sub.type.value.upper()} | {sub.status.value} | " f"{sub.expiry_date.strftime('%d.%m.%Y')}\n"

        # Payments
        text += f"\n💰 <b>Платежи ({len(payments)})</b>\n"
        for payment in payments[:10]:  # Last 10
            text += (
                f"  • {payment.amount} {payment.currency} | "
                f"{payment.status.value} | {payment.created_at.strftime('%d.%m.%Y')}\n"
            )

        await message.answer(text)
