"""Admin data export functionality."""

import csv
import io
import json
import logging
from datetime import datetime
from typing import List

from sqlalchemy import select

from src.core.database import get_session
from src.models.payment import Payment
from src.models.subscription import Subscription
from src.models.user import User

logger = logging.getLogger(__name__)


async def export_users_to_csv() -> str:
    """
    Export users to CSV format.

    Returns:
        CSV content as string
    """
    async for session in get_session():
        result = await session.execute(select(User).order_by(User.created_at.desc()))
        users = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "ID",
                "Telegram ID",
                "Username",
                "Referral Code",
                "Referred By",
                "Created At",
            ]
        )

        # Data
        for user in users:
            writer.writerow(
                [
                    user.id,
                    user.telegram_id,
                    f"@{user.username}" if user.username else "",
                    user.referral_code or "",
                    user.referred_by or "",
                    user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        return output.getvalue()

    return ""


async def export_subscriptions_to_csv() -> str:
    """
    Export subscriptions to CSV format.

    Returns:
        CSV content as string
    """
    async for session in get_session():
        result = await session.execute(select(Subscription).order_by(Subscription.created_at.desc()))
        subscriptions = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "ID",
                "User ID",
                "Type",
                "Status",
                "Start Date",
                "Expiry Date",
                "Traffic Limit",
                "Traffic Used",
                "Link",
            ]
        )

        # Data
        for sub in subscriptions:
            writer.writerow(
                [
                    sub.id,
                    sub.user_id,
                    sub.type.value,
                    sub.status.value,
                    sub.start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    sub.expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
                    sub.traffic_limit or "Unlimited",
                    sub.traffic_used,
                    sub.link[:50] + "..." if sub.link and len(sub.link) > 50 else sub.link,
                ]
            )

        return output.getvalue()

    return ""


async def export_payments_to_csv() -> str:
    """
    Export payments to CSV format.

    Returns:
        CSV content as string
    """
    async for session in get_session():
        result = await session.execute(select(Payment).order_by(Payment.created_at.desc()))
        payments = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "ID",
                "User ID",
                "Amount",
                "Currency",
                "Status",
                "Provider",
                "External ID",
                "Created At",
            ]
        )

        # Data
        for payment in payments:
            writer.writerow(
                [
                    payment.id,
                    payment.user_id,
                    float(payment.amount),
                    payment.currency,
                    payment.status.value,
                    payment.provider.value,
                    payment.external_id or "",
                    payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        return output.getvalue()

    return ""


async def get_revenue_by_period(days: int = 30) -> dict:
    """
    Get revenue statistics for a period.

    Args:
        days: Number of days

    Returns:
        Revenue statistics dictionary
    """
    from datetime import timedelta

    async for session in get_session():
        from src.models.payment import PaymentStatus

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await session.execute(
            select(Payment).where(
                Payment.status == PaymentStatus.paid,
                Payment.created_at >= cutoff_date,
            )
        )
        payments = result.scalars().all()

        total_revenue = sum(p.amount for p in payments)
        by_provider = {}
        by_currency = {}

        for payment in payments:
            # By provider
            provider = payment.provider.value
            by_provider[provider] = by_provider.get(provider, 0) + float(payment.amount)

            # By currency
            currency = payment.currency
            by_currency[currency] = by_currency.get(currency, 0) + float(payment.amount)

        return {
            "period_days": days,
            "total_revenue": float(total_revenue),
            "payment_count": len(payments),
            "by_provider": by_provider,
            "by_currency": by_currency,
            "average_payment": float(total_revenue) / len(payments) if payments else 0,
        }

    return {}


async def get_user_statistics() -> dict:
    """
    Get user statistics.

    Returns:
        User statistics dictionary
    """
    async for session in get_session():
        result = await session.execute(select(User))
        users = result.scalars().all()

        # New users by month
        new_users_by_month = {}
        for user in users:
            month = user.created_at.strftime("%Y-%m")
            new_users_by_month[month] = new_users_by_month.get(month, 0) + 1

        # Referral stats
        referred_count = sum(1 for u in users if u.referred_by)

        return {
            "total_users": len(users),
            "new_users_by_month": new_users_by_month,
            "referred_users": referred_count,
            "referral_rate": (referred_count / len(users) * 100) if users else 0,
        }

    return {}


async def get_subscription_statistics() -> dict:
    """
    Get subscription statistics.

    Returns:
        Subscription statistics dictionary
    """
    async for session in get_session():
        result = await session.execute(select(Subscription))
        subscriptions = result.scalars().all()

        by_type = {}
        by_status = {}
        active_count = 0

        for sub in subscriptions:
            # By type
            sub_type = sub.type.value
            by_type[sub_type] = by_type.get(sub_type, 0) + 1

            # By status
            status = sub.status.value
            by_status[status] = by_status.get(status, 0) + 1

            if status == "active":
                active_count += 1

        return {
            "total_subscriptions": len(subscriptions),
            "active_subscriptions": active_count,
            "by_type": by_type,
            "by_status": by_status,
            "activation_rate": (active_count / len(subscriptions) * 100) if subscriptions else 0,
        }

    return {}
