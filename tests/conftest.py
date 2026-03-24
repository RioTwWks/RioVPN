"""Test fixtures and utilities."""

import asyncio
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.database import Base, get_session
from src.models.payment import Payment, PaymentProvider, PaymentStatus
from src.models.referral import Referral
from src.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from src.models.user import User
from src.services.hiddify import HiddifyService
from src.services.subscription import SubscriptionService
from src.services.three_xui import ThreeXuiService


def pytest_load_initial_conftests(early_config, parser, args):
    """Set environment variables before any imports."""
    os.environ["BOT_TOKEN"] = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    os.environ["PANEL_3XUI_URL"] = "http://test:2096"
    os.environ["PANEL_3XUI_USER"] = "admin"
    os.environ["PANEL_3XUI_PASS"] = "admin123"
    os.environ["INBOUND_RU_TAG"] = "xhttp-ru"
    os.environ["SNI_RU"] = "test.com"
    os.environ["PUBLIC_KEY_RU"] = "test-public-key"
    os.environ["SHORT_ID_RU"] = "abcd1234"
    os.environ["SERVER_ADDRESS_RU"] = "test.com"
    os.environ["SERVER_PORT_RU"] = "8443"
    os.environ["PANEL_HIDDIFY_URL"] = "http://test:8080"
    os.environ["PANEL_HIDDIFY_API_KEY"] = "test-api-key"
    os.environ["ADMIN_TELEGRAM_ID"] = "123456789"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["CRYPTOMUS_API_KEY"] = "test-key"
    os.environ["YOOKASSA_SHOP_ID"] = "test-shop-id"
    os.environ["YOOKASSA_SECRET_KEY"] = "test-secret-key"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_url() -> str:
    """Get test database URL."""
    return "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine(test_db_url: str):
    """Create test database engine."""
    engine = create_async_engine(test_db_url, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        telegram_id=123456789,
        username="testuser",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def subscription(db_session: AsyncSession, user: User) -> Subscription:
    """Create test subscription."""
    subscription = Subscription(
        user_id=user.id,
        type=SubscriptionType.ru,
        status=SubscriptionStatus.active,
        start_date=datetime.utcnow(),
        expiry_date=datetime.utcnow() + timedelta(days=30),
        traffic_limit=100 * 1024**3,  # 100 GB
        traffic_used=0,
        panel_uuid="test-uuid-123",
        link="vless://test-link",
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


@pytest_asyncio.fixture
async def payment(db_session: AsyncSession, user: User) -> Payment:
    """Create test payment."""
    payment = Payment(
        user_id=user.id,
        amount=Decimal("299.00"),
        currency="RUB",
        status=PaymentStatus.paid,
        provider=PaymentProvider.cryptomus,
        external_id="test-payment-123",
        description="Subscription: ru_1",
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


@pytest_asyncio.fixture
async def referral(db_session: AsyncSession, user: User) -> Referral:
    """Create test referral."""
    referred_user = User(telegram_id=999888777, username="referred_user")
    db_session.add(referred_user)
    await db_session.commit()

    referral = Referral(
        referrer_id=user.telegram_id,
        referred_id=referred_user.telegram_id,
        bonus_amount=Decimal("50.00"),
    )
    db_session.add(referral)
    await db_session.commit()
    await db_session.refresh(referral)
    return referral


@pytest.fixture
def mock_bot() -> MagicMock:
    """Create mock bot."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))
    return bot


@pytest.fixture
def mock_callback_query(mock_bot: MagicMock) -> MagicMock:
    """Create mock callback query."""
    callback = MagicMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = MagicMock(id=123456789)
    callback.bot = mock_bot
    callback.data = "test_callback"
    return callback


@pytest.fixture
def mock_message(mock_bot: MagicMock) -> MagicMock:
    """Create mock message."""
    message = MagicMock()
    message.answer = AsyncMock()
    message.from_user = MagicMock(id=123456789, username="testuser")
    message.text = "/start"
    message.bot = mock_bot
    return message


@pytest.fixture
def mock_three_xui() -> MagicMock:
    """Create mock 3x-ui service."""
    service = MagicMock(spec=ThreeXuiService)
    service.get_inbounds = AsyncMock(return_value=[{"id": 1, "tag": "xhttp-ru", "settings": {"clients": []}}])
    service.add_client = AsyncMock(return_value=True)
    service.delete_client = AsyncMock(return_value=True)
    service.get_client_traffic = AsyncMock(return_value={"total": 1024})
    service.update_client = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_hiddify() -> MagicMock:
    """Create mock Hiddify service."""
    service = MagicMock(spec=HiddifyService)
    service.create_user = AsyncMock(
        return_value={
            "uuid": "test-uuid-123",
            "subscription_url": "https://test.com/sub/uuid",
        }
    )
    service.get_user = AsyncMock(
        return_value={
            "uuid": "test-uuid-123",
            "used_traffic": 1024,
        }
    )
    service.delete_user = AsyncMock(return_value=True)
    service.update_user = AsyncMock(return_value=True)
    service.get_user_traffic = AsyncMock(return_value={"used": 1024})
    return service


@pytest_asyncio.fixture
async def subscription_service(
    db_session: AsyncSession,
    mock_three_xui: MagicMock,
    mock_hiddify: MagicMock,
) -> SubscriptionService:
    """Create subscription service with mocked panels."""
    with patch.object(SubscriptionService, "__init__", lambda self, session: None):
        service = SubscriptionService(db_session)
        service.three_xui = mock_three_xui
        service.hiddify = mock_hiddify
        service.session = db_session
        return service
