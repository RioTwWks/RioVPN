# RioVPN - Telegram VPN Subscription Bot

## Project Overview

**RioVPN** is a Telegram bot that automates the sale of VPN subscriptions. The bot integrates with two VPN panel systems to provide users with ready-to-use VPN connections after payment.

### Core Features

- **Two Subscription Types:**
  - **Type A (RU)**: Russian VPS via 3x-ui panel (VLESS + Reality + XHTTP protocol) for bypassing mobile operator whitelists
  - **Type B (EU)**: European VPS via Hiddify-Manager panel for global internet access

- **Key Capabilities:**
  - Individual user creation in respective panels for each customer
  - Automatic vless:// link generation after successful payment
  - Subscription renewal with automatic expiry handling
  - Traffic limit monitoring and enforcement
  - Multiple payment gateway integration (Cryptomus, YooKassa, Telegram Stars)
  - Background worker for subscription lifecycle management

### Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Bot Framework | aiogram 3.x |
| HTTP Client | aiohttp |
| Database | SQLite (async) |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Background Tasks | APScheduler / asyncio |
| Testing | pytest, pytest-asyncio, pytest-cov |
| Validation | Pydantic 2.x |

---

## Project Structure

```
RioVPN/
├── src/
│   ├── bot/           # Telegram handlers, keyboards, middlewares
│   ├── core/          # Configuration, database connection, logging
│   ├── services/      # External API clients (3x-ui, Hiddify, Payments)
│   ├── models/        # SQLAlchemy ORM models
│   ├── utils/         # Helper functions, validators
│   └── workers/       # Background tasks and schedulers
├── tests/             # Test suite
├── migrations/        # Alembic database migrations
├── .qwen/             # Qwen agent configuration
├── .env.example       # Environment variable template
├── requirements.txt   # Python dependencies
├── pytest.ini         # Pytest configuration
├── spec.md            # Detailed project specification (Russian)
└── README.md          # Quick start guide
```

---

## Building and Running

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional, for containerized deployment)

### Quick Start

1. **Clone and setup environment:**
   ```bash
   cp .env.example .env
   # Fill in .env with your configuration
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the bot:**
   ```bash
   python -m src.bot.main
   ```

4. **Run the background worker:**
   ```bash
   python -m src.workers.scheduler
   ```

### Docker Deployment

```bash
docker-compose up -d
```

### Running Tests

```bash
pytest
# With coverage
pytest --cov=src --cov-report=html
```

### Database Migrations

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

---

## Configuration

### Environment Variables

See `.env.example` for all required variables:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `PANEL_3XUI_URL` | 3x-ui panel URL (e.g., `http://ru-vps:2096`) |
| `PANEL_3XUI_USER` | 3x-ui admin username |
| `PANEL_3XUI_PASS` | 3x-ui admin password |
| `INBOUND_RU_TAG` | 3x-ui inbound tag for RU clients |
| `SNI_RU` | SNI domain for Reality protocol |
| `PUBLIC_KEY_RU` | Reality public key |
| `SHORT_ID_RU` | Reality short ID |
| `SERVER_ADDRESS_RU` | Russian server IP/domain |
| `SERVER_PORT_RU` | Russian server port |
| `PANEL_HIDDIFY_URL` | Hiddify panel URL |
| `PANEL_HIDDIFY_API_KEY` | Hiddify admin API key |
| `CRYPTOMUS_API_KEY` | Cryptomus payment API key |
| `YOOKASSA_SHOP_ID` | YooKassa shop ID |
| `YOOKASSA_SECRET_KEY` | YooKassa secret key |
| `ADMIN_TELEGRAM_ID` | Admin Telegram ID for admin commands |
| `DATABASE_URL` | Database connection string |
| `DEFAULT_TRAFFIC_LIMIT_RU` | Default RU traffic limit in bytes (empty = unlimited) |
| `DEFAULT_TRAFFIC_LIMIT_EU` | Default EU traffic limit in bytes (empty = unlimited) |

---

## Database Models

### Core Models

```python
User
├── id (Integer, PK)
├── telegram_id (BigInteger, unique)
├── username (String)
└── created_at (DateTime)

Subscription
├── id (Integer, PK)
├── user_id (FK -> User.id)
├── type (Enum: 'ru', 'eu')
├── status (Enum: 'active', 'expired', 'blocked')
├── start_date (DateTime)
├── expiry_date (DateTime)
├── traffic_limit (BigInteger, nullable)
├── traffic_used (BigInteger)
├── panel_uuid (String) - Hiddify UUID or 3x-ui email
├── inbound_tag (String) - 3x-ui inbound tag
└── link (Text) - vless:// subscription link

Payment
├── id (Integer, PK)
├── user_id (FK -> User.id)
├── amount (Float)
├── currency (String)
├── status (String)
├── external_id (String)
└── created_at (DateTime)

Settings
├── key (String, PK)
├── value (Text)
└── updated_at (DateTime)
```

---

## API Integrations

### 3x-ui API (RU Panel)

**Base URL:** `PANEL_3XUI_URL`
**Authentication:** Basic Auth (username/password)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/panel/api/inbounds/list` | GET | List all inbounds and clients |
| `/panel/api/inbounds/addClient` | POST | Add client to existing inbound |
| `/panel/api/inbounds/updateClient` | POST | Update client limits |
| `/panel/api/inbounds/delClient` | POST | Remove client |
| `/panel/api/inbounds/getClientTraffic/:email` | GET | Get client traffic usage |

### Hiddify API (EU Panel)

**Base URL:** `PANEL_HIDDIFY_URL/api/v2/`
**Authentication:** Header `Hiddify-API-Key: <UUID>`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/user/` | POST | Create new user |
| `/admin/user/<uuid>` | GET | Get user info |
| `/admin/user/<uuid>` | PUT | Update user (extend, change limits) |
| `/admin/user/<uuid>` | DELETE | Remove user |
| `/admin/users/` | GET | List all users |

---

## Bot Commands

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message, subscription selection menu |
| `/buy` | Purchase new subscription (select type and duration) |
| `/my` | View current subscription status and traffic usage |
| `/renew` | Renew existing subscription |
| `/support` | Contact support |
| `/referral` | Referral program information |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/stats` | Sales and traffic statistics |
| `/broadcast` | Send message to all users |
| `/suspend <telegram_id>` | Suspend user subscription |
| `/grant <telegram_id> [type] [days]` | Manually grant subscription |

---

## Background Worker Tasks

| Task | Frequency | Description |
|------|-----------|-------------|
| `check_expiring_subscriptions` | Hourly | Check subscriptions expiring soon |
| `sync_traffic` | Daily | Sync traffic usage from panels |
| `send_reminders` | Daily | Send expiry reminders (3 days before) |
| `process_webhooks` | Async | Handle payment gateway callbacks |

---

## Development Conventions

### Code Style

- **Type Hints:** Required for all function signatures
- **Docstrings:** Google style for all public functions and classes
- **Async:** All I/O operations must be async (HTTP, DB, file system)
- **Error Handling:** Use custom exceptions with proper logging

### Example Pattern

```python
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """
    Retrieve user by Telegram ID.

    Args:
        session: Async database session
        telegram_id: User's Telegram ID

    Returns:
        User object or None if not found
    """
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()
```

### Testing Practices

- Use `pytest-asyncio` for async tests
- Mock external API calls
- Test critical paths: payment, subscription creation, renewal
- Minimum coverage target: 80% for core services

### Security Rules

- Never hardcode secrets - use environment variables only
- Admin commands restricted by Telegram ID whitelist
- All API calls to panels use retry logic (tenacity)
- Input validation via Pydantic models
- Proper error logging without exposing sensitive data

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `spec.md` | Detailed project specification (in Russian) |
| `requirements.txt` | Python package dependencies |
| `.env.example` | Environment variable template |
| `pytest.ini` | Pytest configuration |
| `.qwen/rules.md` | Development rules and coding standards |
| `.qwen/workflows.json` | Qwen agent workflows |
| `.qwen/troubleshooting.md` | Common issues and solutions |

---

## Useful Links

- [aiogram 3.x Documentation](https://docs.aiogram.dev/)
- [SQLAlchemy 2.x Documentation](https://docs.sqlalchemy.org/)
- [3x-ui GitHub](https://github.com/MHSanaei/3x-ui)
- [Hiddify Manager GitHub](https://github.com/hiddify/hiddify-manager)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
