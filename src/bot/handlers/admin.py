"""Admin command handlers."""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlalchemy import select

from src.bot.handlers.export import (
    export_payments_to_csv,
    export_subscriptions_to_csv,
    export_users_to_csv,
    get_revenue_by_period,
    get_subscription_statistics,
    get_user_statistics,
)
from src.bot.keyboards import get_admin_keyboard
from src.core.config import settings
from src.core.database import get_session
from src.models.payment import Payment, PaymentStatus
from src.models.subscription import Subscription, SubscriptionStatus
from src.models.user import User

logger = logging.getLogger(__name__)

admin_router = Router()


async def is_admin(user_id: int) -> bool:
    """
    Check if user is admin.

    Args:
        user_id: Telegram user ID

    Returns:
        True if user is admin
    """
    admin_id = settings.admin_telegram_id
    if admin_id is None:
        return False
    return user_id == admin_id


@admin_router.message(Command("admin"))
async def handle_admin(message: Message) -> None:
    """
    Handle /admin command - show admin panel.

    Args:
        message: Incoming message
    """
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(),
    )


@admin_router.message(Command("stats"))
async def handle_stats(message: Message) -> None:
    """
    Handle /stats command - show statistics.

    Args:
        message: Incoming message
    """
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    async for session in get_session():
        # Count users
        user_count = await session.execute(select(User))
        total_users = len(user_count.scalars().all())

        # Count subscriptions
        subs_result = await session.execute(select(Subscription))
        subscriptions = subs_result.scalars().all()

        active_subs = sum(1 for s in subscriptions if s.status == SubscriptionStatus.active)
        expired_subs = sum(1 for s in subscriptions if s.status == SubscriptionStatus.expired)
        blocked_subs = sum(1 for s in subscriptions if s.status == SubscriptionStatus.blocked)

        # Count payments
        payments_result = await session.execute(select(Payment))
        payments = payments_result.scalars().all()

        paid_payments = sum(1 for p in payments if p.status == PaymentStatus.paid)
        pending_payments = sum(1 for p in payments if p.status == PaymentStatus.pending)
        total_revenue = sum(
            float(p.amount) for p in payments if p.status == PaymentStatus.paid
        )

        await message.answer(
            f"📊 <b>Статистика</b>\n\n"
            f"👥 <b>Пользователи:</b> {total_users}\n\n"
            f"📱 <b>Подписки:</b>\n"
            f"  • Активные: {active_subs}\n"
            f"  • Истёкшие: {expired_subs}\n"
            f"  • Заблокированные: {blocked_subs}\n"
            f"  • Всего: {len(subscriptions)}\n\n"
            f"💰 <b>Платежи:</b>\n"
            f"  • Оплачено: {paid_payments}\n"
            f"  • Ожидают: {pending_payments}\n"
            f"  • Выручка: {total_revenue:.2f} ₽"
        )


@admin_router.message(Command("pending"))
async def handle_pending(message: Message) -> None:
    """
    Handle /pending command - show pending payments.

    Args:
        message: Incoming message
    """
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    # Note: In MVP, all subscriptions are created immediately
    # This will be used when automatic payments are implemented
    await message.answer(
        "⏳ <b>Ожидающие оплаты</b>\n\n"
        "В текущей версии подписки создаются сразу после оплаты.\n"
        "Раздел будет доступен после внедрения автоматических платежей."
    )


@admin_router.message(Command("suspend"))
async def handle_suspend(message: Message) -> None:
    """
    Handle /suspend command - suspend user subscription.

    Usage: /suspend <telegram_id>

    Args:
        message: Incoming message
    """
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    # Parse telegram_id from command args
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /suspend <telegram_id>\n"
            "Пример: /suspend 123456789"
        )
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат Telegram ID")
        return

    async for session in get_session():
        # Find user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(f"❌ Пользователь {telegram_id} не найден")
            return

        # Find active subscription
        result = await session.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .where(Subscription.status == SubscriptionStatus.active)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            await message.answer("❌ У пользователя нет активной подписки")
            return

        # Block subscription
        subscription.status = SubscriptionStatus.blocked
        await session.commit()

        await message.answer(
            f"✅ Подписка пользователя {telegram_id} заблокирована"
        )

        logger.info(
            f"Admin {message.from_user.id} suspended subscription "
            f"{subscription.id} for user {telegram_id}"
        )


@admin_router.message(Command("grant"))
async def handle_grant(message: Message) -> None:
    """
    Handle /grant command - grant free subscription.

    Usage: /grant <telegram_id> [type] [days]

    Args:
        message: Incoming message
    """
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /grant <telegram_id> [type] [days]\n"
            "Пример: /grant 123456789 ru 30"
        )
        return

    try:
        telegram_id = int(args[1])
        sub_type = args[2] if len(args) > 2 else "ru"
        days = int(args[3]) if len(args) > 3 else 30
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат аргументов")
        return

    if sub_type not in ["ru", "eu"]:
        await message.answer("❌ Тип должен быть 'ru' или 'eu'")
        return

    async for session in get_session():
        # Find or create user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Create free subscription
        from src.services.subscription import SubscriptionService
        from src.models.subscription import SubscriptionType

        service = SubscriptionService(session)

        try:
            subscription = await service.create_subscription(
                user=user,
                sub_type=SubscriptionType(sub_type),
                duration_days=days,
            )

            await message.answer(
                f"✅ Выдана подписка пользователю {telegram_id}\n\n"
                f"Тип: {sub_type.upper()}\n"
                f"Срок: {days} дней\n"
                f"ID подписки: {subscription.id}"
            )

            logger.info(
                f"Admin {message.from_user.id} granted subscription "
                f"to user {telegram_id}: type={sub_type}, days={days}"
            )

        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")


@admin_router.message(Command("export"))
async def handle_export(message: Message) -> None:
    """
    Handle /export command - export data to CSV.

    Usage: /export [users|subscriptions|payments]

    Args:
        message: Incoming message
    """
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    args = message.text.split()
    export_type = args[1] if len(args) > 1 else "users"

    await message.answer(f"⏳ <b>Генерация экспорта: {export_type}...</b>")

    try:
        if export_type == "users":
            csv_data = await export_users_to_csv()
            filename = f"users_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        elif export_type == "subscriptions":
            csv_data = await export_subscriptions_to_csv()
            filename = f"subscriptions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        elif export_type == "payments":
            csv_data = await export_payments_to_csv()
            filename = f"payments_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            await message.answer(
                "❌ Неверный тип. Доступные: users, subscriptions, payments"
            )
            return

        # Send file
        await message.answer_document(
            document=BufferedInputFile(csv_data.encode(), filename=filename),
            caption=f"📊 <b>Экспорт: {export_type}</b>\n{len(csv_data.splitlines()) - 1} записей",
        )

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка экспорта: {e}")


@admin_router.message(Command("analytics"))
async def handle_analytics(message: Message) -> None:
    """
    Handle /analytics command - show detailed analytics.

    Args:
        message: Incoming message
    """
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    # Get statistics
    user_stats = await get_user_statistics()
    sub_stats = await get_subscription_statistics()
    revenue_stats = await get_revenue_by_period(30)

    text = (
        f"📊 <b>Аналитика</b>\n\n"
        f"👥 <b>Пользователи</b>\n"
        f"• Всего: {user_stats.get('total_users', 0)}\n"
        f"• По рефералке: {user_stats.get('referred_users', 0)} ({user_stats.get('referral_rate', 0):.1f}%)\n\n"
        f"📱 <b>Подписки</b>\n"
        f"• Всего: {sub_stats.get('total_subscriptions', 0)}\n"
        f"• Активных: {sub_stats.get('active_subscriptions', 0)} ({sub_stats.get('activation_rate', 0):.1f}%)\n\n"
        f"💰 <b>Выручка (30 дней)</b>\n"
        f"• Всего: {revenue_stats.get('total_revenue', 0):.2f} ₽\n"
        f"• Платежей: {revenue_stats.get('payment_count', 0)}\n"
        f"• Средний чек: {revenue_stats.get('average_payment', 0):.2f} ₽\n\n"
        f"📊 <b>По провайдерам</b>\n"
    )

    for provider, amount in revenue_stats.get('by_provider', {}).items():
        text += f"• {provider}: {amount:.2f} ₽\n"

    await message.answer(text)
