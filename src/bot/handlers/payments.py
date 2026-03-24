"""Admin payment history handlers."""

import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from src.bot.keyboards import get_back_keyboard
from src.core.database import get_session
from src.core.logging import get_logger
from src.models.payment import Payment, PaymentStatus

logger = get_logger(__name__)

payment_history_router = Router()


@payment_history_router.callback_query(F.data == "admin_payments")
async def handle_admin_payments(callback: CallbackQuery) -> None:
    """
    Handle admin payments list command.

    Args:
        callback: Callback query
    """
    async for session in get_session():
        result = await session.execute(select(Payment).order_by(Payment.created_at.desc()).limit(20))
        payments = result.scalars().all()

        text = "💰 <b>Платежи (последние 20)</b>\n\n"

        for payment in payments:
            status_emoji = get_status_emoji(payment.status)
            provider_emoji = "🔐" if payment.provider.value == "cryptomus" else "💳"

            text += (
                f"{status_emoji} <b>ID:</b> {payment.id}\n"
                f"💰 <b>Сумма:</b> {payment.amount} {payment.currency}\n"
                f"{provider_emoji} <b>Провайдер:</b> {payment.provider.value}\n"
                f"📊 <b>Статус:</b> {payment.status.value}\n"
                f"📅 <b>Дата:</b> {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )

        # Calculate totals
        total_result = await session.execute(select(Payment).where(Payment.status == PaymentStatus.paid))
        paid_payments = total_result.scalars().all()
        total_revenue = sum(p.amount for p in paid_payments)

        text += f"💵 <b>Общая выручка:</b> {total_revenue} RUB\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard(),
        )

    await callback.answer()


@payment_history_router.message(Command("payments"))
async def handle_payments_command(message: Message) -> None:
    """
    Handle /payments command - list payments.

    Usage: /payments [limit] [status]

    Args:
        message: Incoming message
    """
    args = message.text.split()
    limit = int(args[1]) if len(args) > 1 else 20
    status_filter = args[2] if len(args) > 2 else None

    async for session in get_session():
        query = select(Payment).order_by(Payment.created_at.desc()).limit(limit)

        if status_filter:
            try:
                status = PaymentStatus(status_filter)
                query = query.where(Payment.status == status)
            except ValueError:
                await message.answer(f"❌ Неверный статус. Доступные: {', '.join(s.value for s in PaymentStatus)}")
                return

        result = await session.execute(query)
        payments = result.scalars().all()

        text = f"💰 <b>Платежи"
        if status_filter:
            text += f" ({status_filter})"
        text += f" (последние {limit})</b>\n\n"

        for payment in payments:
            status_emoji = get_status_emoji(payment.status)
            text += (
                f"{status_emoji} #{payment.id} | {payment.amount} {payment.currency} | "
                f"{payment.provider.value} | {payment.status.value} | "
                f"{payment.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            )

        await message.answer(text)


@payment_history_router.message(Command("revenue"))
async def handle_revenue_command(message: Message) -> None:
    """
    Handle /revenue command - show revenue statistics.

    Args:
        message: Incoming message
    """
    async for session in get_session():
        # Total revenue
        result = await session.execute(select(Payment).where(Payment.status == PaymentStatus.paid))
        paid_payments = result.scalars().all()
        total_revenue = sum(p.amount for p in paid_payments)

        # By provider
        cryptomus_revenue = sum(p.amount for p in paid_payments if p.provider.value == "cryptomus")
        yookassa_revenue = sum(p.amount for p in paid_payments if p.provider.value == "yookassa")

        # Today's revenue
        from datetime import date

        today = date.today()
        result = await session.execute(
            select(Payment).where(
                Payment.status == PaymentStatus.paid,
                Payment.created_at >= today,
            )
        )
        today_payments = result.scalars().all()
        today_revenue = sum(p.amount for p in today_payments)

        # This month
        from datetime import datetime

        first_day = datetime(today.year, today.month, 1)
        result = await session.execute(
            select(Payment).where(
                Payment.status == PaymentStatus.paid,
                Payment.created_at >= first_day,
            )
        )
        month_payments = result.scalars().all()
        month_revenue = sum(p.amount for p in month_payments)

        text = (
            f"💰 <b>Статистика выручки</b>\n\n"
            f"💵 <b>Всего:</b> {total_revenue} RUB\n"
            f"📅 <b>Сегодня:</b> {today_revenue} RUB ({len(today_payments)} платежей)\n"
            f"📅 <b>Этот месяц:</b> {month_revenue} RUB ({len(month_payments)} платежей)\n\n"
            f"🔐 <b>Cryptomus:</b> {cryptomus_revenue} RUB\n"
            f"💳 <b>ЮKassa:</b> {yookassa_revenue} RUB\n\n"
            f"✅ <b>Всего оплат:</b> {len(paid_payments)}"
        )

        await message.answer(text)


def get_status_emoji(status: PaymentStatus) -> str:
    """Get emoji for payment status."""
    emojis = {
        PaymentStatus.pending: "⏳",
        PaymentStatus.paid: "✅",
        PaymentStatus.failed: "❌",
        PaymentStatus.refunded: "↩️",
    }
    return emojis.get(status, "❓")
