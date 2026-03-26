"""Admin test panel for testing payment flows and subscriptions."""

import logging
from datetime import timedelta
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from src.bot.keyboards import get_admin_back_keyboard
from src.core.database import get_session
from src.core.logging import get_logger
from src.models.user import User
from src.models.subscription import Subscription, SubscriptionType, SubscriptionStatus
from src.models.payment import Payment, PaymentProvider, PaymentStatus
from src.services.subscription import SubscriptionService

logger = get_logger(__name__)

test_router = Router()


async def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    from src.core.config import settings

    admin_id = settings.admin_telegram_id
    if admin_id is None:
        return False
    return user_id == admin_id


@test_router.message(Command("test"))
async def handle_test(message: Message) -> None:
    """Handle /test command - show test panel."""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🧪 Тестовый пользователь", callback_data="test_create_user")
    builder.button(text="💳 Тестовая оплата", callback_data="test_create_payment")
    builder.button(text="📱 RU Подписка", callback_data="test_create_subscription_ru")
    builder.button(text="🇪🇺 EU Подписка", callback_data="test_create_subscription_eu")
    builder.button(text="🗑 Очистить тест", callback_data="test_cleanup")
    builder.button(text="📊 Статус", callback_data="test_status")
    builder.button(text="« Назад в админ-панель", callback_data="admin_menu")
    builder.adjust(2, 2, 2, 1)

    await message.answer(
        "🧪 <b>Тестовая панель</b>\n\n"
        "Инструменты для тестирования платежных потоков:\n\n"
        "• <b>Тестовый пользователь</b> - создаёт тестового юзера\n"
        "• <b>Тестовая оплата</b> - имитирует успешную оплату\n"
        "• <b>RU Подписка</b> - создаёт российскую подписку (3x-ui)\n"
        "• <b>EU Подписка</b> - создаёт европейскую подписку (Hiddify)\n"
        "• <b>Очистить тест</b> - удаляет тестовые данные\n"
        "• <b>Статус</b> - показывает текущее состояние",
        reply_markup=builder.as_markup(),
    )


@test_router.callback_query(F.data == "test_create_user")
async def handle_test_create_user(callback: CallbackQuery) -> None:
    """Handle test user creation."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    async for session in get_session():
        # Create test user
        test_telegram_id = 999999999
        result = await session.execute(select(User).where(User.telegram_id == test_telegram_id))
        user = result.scalar_one_or_none()

        if user:
            await callback.message.answer(
                "ℹ️ <b>Тестовый пользователь уже существует</b>\n\n"
                f"ID: <code>{user.id}</code>\n"
                f"Telegram ID: <code>{user.telegram_id}</code>\n"
                f"Username: {user.username or 'N/A'}"
            )
        else:
            user = User(
                telegram_id=test_telegram_id,
                username="test_user",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            await callback.message.answer(
                "✅ <b>Тестовый пользователь создан</b>\n\n"
                f"ID: <code>{user.id}</code>\n"
                f"Telegram ID: <code>{user.telegram_id}</code>\n"
                f"Username: test_user"
            )

    await callback.answer()


@test_router.callback_query(F.data == "test_create_payment")
async def handle_test_create_payment(callback: CallbackQuery) -> None:
    """Handle test payment creation."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    async for session in get_session():
        # Find or create test user
        test_telegram_id = 999999999
        result = await session.execute(select(User).where(User.telegram_id == test_telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=test_telegram_id, username="test_user")
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Create test payment
        import random

        payment = Payment(
            user_id=user.id,
            amount=random.choice([299, 499, 799, 1299, 2699]),
            currency="RUB",
            status=PaymentStatus.paid,
            provider=PaymentProvider.cryptomus,
            external_id=f"test_{random.randint(10000, 99999)}",
        )
        session.add(payment)
        await session.commit()

        await callback.message.answer(
            "✅ <b>Тестовая оплата создана</b>\n\n"
            f"ID: <code>{payment.id}</code>\n"
            f"Сумма: {payment.amount} {payment.currency}\n"
            f"Статус: {payment.status.value}\n"
            f"Провайдер: {payment.provider.value}\n"
            f"External ID: {payment.external_id}"
        )

    await callback.answer()


@test_router.callback_query(F.data == "test_create_subscription_ru")
async def handle_test_create_subscription_ru(callback: CallbackQuery) -> None:
    """Handle test RU subscription creation."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await create_test_subscription(callback, SubscriptionType.ru, "🇷🇺 RU")


@test_router.callback_query(F.data == "test_create_subscription_eu")
async def handle_test_create_subscription_eu(callback: CallbackQuery) -> None:
    """Handle test EU subscription creation."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await create_test_subscription(callback, SubscriptionType.eu, "🇪🇺 EU")


async def create_test_subscription(callback: CallbackQuery, sub_type: SubscriptionType, type_emoji: str) -> None:
    """Create test subscription helper."""
    async for session in get_session():
        # Find or create test user
        test_telegram_id = 999999999
        result = await session.execute(select(User).where(User.telegram_id == test_telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=test_telegram_id, username="test_user")
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Create test subscription
        service = SubscriptionService(session)

        try:
            subscription = await service.create_subscription(
                user=user,
                sub_type=sub_type,
                duration_days=30,
            )

            await callback.message.answer(
                f"✅ <b>Тестовая {type_emoji} подписка создана</b>\n\n"
                f"ID: <code>{subscription.id}</code>\n"
                f"Тип: {subscription.type.value.upper()}\n"
                f"Статус: {subscription.status.value}\n"
                f"Действует до: {subscription.expiry_date.strftime('%d.%m.%Y')}\n"
                f"Осталось дней: {subscription.days_remaining}\n\n"
                f"🔗 <b>Ссылка:</b>\n<code>{subscription.link}</code>"
            )
        except Exception as e:
            logger.exception(f"Failed to create {sub_type.value} subscription")
            await callback.message.answer(f"❌ Ошибка создания {type_emoji} подписки: {e}")

    await callback.answer()


@test_router.callback_query(F.data == "test_cleanup")
async def handle_test_cleanup(callback: CallbackQuery) -> None:
    """Handle test data cleanup."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    async for session in get_session():
        # Find and delete test user
        test_telegram_id = 999999999
        result = await session.execute(select(User).where(User.telegram_id == test_telegram_id))
        user = result.scalar_one_or_none()

        if user:
            # Delete subscriptions
            await session.execute(select(Subscription).where(Subscription.user_id == user.id))
            subscriptions = await session.execute(select(Subscription).where(Subscription.user_id == user.id))
            for sub in subscriptions.scalars().all():
                await session.delete(sub)

            # Delete payments
            payments = await session.execute(select(Payment).where(Payment.user_id == user.id))
            for payment in payments.scalars().all():
                await session.delete(payment)

            # Delete user
            await session.delete(user)
            await session.commit()

            await callback.message.answer("🧹 <b>Тестовые данные очищены</b>")
        else:
            await callback.message.answer("ℹ️ <b>Тестовые данные не найдены</b>")

    await callback.answer()


@test_router.callback_query(F.data == "test_status")
async def handle_test_status(callback: CallbackQuery) -> None:
    """Handle test status view."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    async for session in get_session():
        test_telegram_id = 999999999
        result = await session.execute(select(User).where(User.telegram_id == test_telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.message.answer(
                "ℹ️ <b>Тестовый пользователь не найден</b>\n\n" "Создайте тестового пользователя для начала тестирования."
            )
            return

        # Get subscriptions
        subs_result = await session.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscriptions = subs_result.scalars().all()

        # Get payments
        payments_result = await session.execute(select(Payment).where(Payment.user_id == user.id))
        payments = payments_result.scalars().all()

        text = (
            "📊 <b>Статус тестовых данных</b>\n\n"
            f"👤 <b>Пользователь:</b>\n"
            f"  ID: <code>{user.id}</code>\n"
            f"  Telegram ID: <code>{user.telegram_id}</code>\n\n"
            f"📱 <b>Подписки ({len(subscriptions)})</b>\n"
        )

        for sub in subscriptions:
            text += f"  • {sub.type.value.upper()} | {sub.status.value} | " f"до {sub.expiry_date.strftime('%d.%m.%Y')}\n"

        text += f"\n💰 <b>Платежи ({len(payments)})</b>\n"

        for payment in payments:
            text += f"  • {payment.amount} {payment.currency} | " f"{payment.status.value} | {payment.provider.value}\n"

        if not subscriptions and not payments:
            text += "\nℹ️ Нет активных тестовых данных"

        await callback.message.answer(text)

    await callback.answer()
