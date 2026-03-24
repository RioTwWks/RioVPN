"""Test fixtures and utilities."""

import asyncio
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
    service.get_inbounds = AsyncMock(return_value=[
        {"id": 1, "tag": "xhttp-ru", "settings": {"clients": []}}
    ])
    service.add_client = AsyncMock(return_value=True)
    service.delete_client = AsyncMock(return_value=True)
    service.get_client_traffic = AsyncMock(return_value={"total": 1024})
    service.update_client = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_hiddify() -> MagicMock:
    """Create mock Hiddify service."""
    service = MagicMock(spec=HiddifyService)
    service.create_user = AsyncMock(return_value={
        "uuid": "test-uuid-123",
        "subscription_url": "https://test.com/sub/uuid",
    })
    service.get_user = AsyncMock(return_value={
        "uuid": "test-uuid-123",
        "used_traffic": 1024,
    })
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
    with patch.object(SubscriptionService, '__init__', lambda self, session: None):
        service = SubscriptionService(db_session)
        service.three_xui = mock_three_xui
        service.hiddify = mock_hiddify
        service.session = db_session
        return service


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables for testing."""
    monkeypatch.setenv("BOT_TOKEN", "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
    monkeypatch.setenv("PANEL_3XUI_URL", "http://test:2096")
    monkeypatch.setenv("PANEL_3XUI_USER", "admin")
    monkeypatch.setenv("PANEL_3XUI_PASS", "admin123")
    monkeypatch.setenv("INBOUND_RU_TAG", "xhttp-ru")
    monkeypatch.setenv("SNI_RU", "test.com")
    monkeypatch.setenv("PUBLIC_KEY_RU", "test-public-key")
    monkeypatch.setenv("SHORT_ID_RU", "abcd1234")
    monkeypatch.setenv("SERVER_ADDRESS_RU", "test.com")
    monkeypatch.setenv("SERVER_PORT_RU", "8443")
    monkeypatch.setenv("PANEL_HIDDIFY_URL", "http://test:8080")
    monkeypatch.setenv("PANEL_HIDDIFY_API_KEY", "test-api-key")
    monkeypatch.setenv("ADMIN_TELEGRAM_ID", "123456789")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
