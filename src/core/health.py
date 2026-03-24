"""Health check utilities for the bot."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text

from src.core.database import engine, get_session
from src.core.logging import get_logger
from src.models.subscription import Subscription, SubscriptionStatus

logger = get_logger(__name__)


@dataclass
class HealthStatus:
    """Health check status."""

    status: str  # "healthy", "degraded", "unhealthy"
    checks: Dict[str, Any]
    timestamp: datetime


async def check_database() -> Dict[str, Any]:
    """
    Check database connectivity.

    Returns:
        Database health status
    """
    start_time = time.time()

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            duration = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(duration, 2),
            }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_panel_connections() -> Dict[str, Any]:
    """
    Check VPN panel connections.

    Returns:
        Panel connection status
    """
    from src.services.hiddify import HiddifyService
    from src.services.three_xui import ThreeXuiService

    results = {
        "3x-ui": {"status": "unknown"},
        "hiddify": {"status": "unknown"},
    }

    # Check 3x-ui
    try:
        three_xui = ThreeXuiService()
        await three_xui.get_inbounds()
        results["3x-ui"] = {"status": "healthy"}
    except Exception as e:
        results["3x-ui"] = {"status": "unhealthy", "error": str(e)}

    # Check Hiddify
    try:
        hiddify = HiddifyService()
        await hiddify.get_all_users()
        results["hiddify"] = {"status": "healthy"}
    except Exception as e:
        results["hiddify"] = {"status": "unhealthy", "error": str(e)}

    return results


async def check_subscription_health() -> Dict[str, Any]:
    """
    Check subscription statistics.

    Returns:
        Subscription health metrics
    """
    async for session in get_session():
        try:
            # Count active subscriptions
            result = await session.execute(
                select(Subscription).where(
                    Subscription.status == SubscriptionStatus.active
                )
            )
            active_subs = len(result.scalars().all())

            # Count expiring soon (within 24 hours)
            from datetime import datetime, timedelta

            target_date = datetime.utcnow() + timedelta(hours=24)
            result = await session.execute(
                select(Subscription)
                .where(Subscription.status == SubscriptionStatus.active)
                .where(Subscription.expiry_date <= target_date)
            )
            expiring_soon = len(result.scalars().all())

            return {
                "status": "healthy",
                "active_subscriptions": active_subs,
                "expiring_within_24h": expiring_soon,
            }

        except Exception as e:
            logger.error(f"Subscription health check failed: {e}")
            return {
                "status": "degraded",
                "error": str(e),
            }

    return {"status": "unknown", "error": "Session not available"}


async def get_health_status() -> HealthStatus:
    """
    Get overall system health status.

    Returns:
        Combined health status
    """
    checks: Dict[str, Any] = {}

    # Database check
    checks["database"] = await check_database()

    # Panel connections
    checks["panels"] = await check_panel_connections()

    # Subscription health
    checks["subscriptions"] = await check_subscription_health()

    # Determine overall status
    statuses = []
    for check_name, check_result in checks.items():
        if isinstance(check_result, dict):
            status = check_result.get("status", "unknown")
            statuses.append(status)
        elif hasattr(check_result, "status"):
            statuses.append(check_result.status)

    if "unhealthy" in statuses:
        overall_status = "unhealthy"
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return HealthStatus(
        status=overall_status,
        checks=checks,
        timestamp=datetime.utcnow(),
    )


def format_health_response(health: HealthStatus) -> Dict[str, Any]:
    """
    Format health status for API response.

    Args:
        health: HealthStatus object

    Returns:
        Dictionary for JSON response
    """
    return {
        "status": health.status,
        "timestamp": health.timestamp.isoformat(),
        "checks": health.checks,
    }
