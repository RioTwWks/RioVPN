# RioVPN - Telegram VPN Subscription Bot

## Project Overview

**RioVPN** is a full-featured Telegram bot that automates the sale of VPN subscriptions. The bot integrates with two VPN panel systems to provide users with ready-to-use VPN connections after payment.

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
  - Referral program (10% bonus for each referred user)
  - Multi-language support (Russian/English) via i18n

### Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Bot Framework | aiogram 3.x |
| HTTP Client | aiohttp |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Background Tasks | APScheduler 4.x |
| Testing | pytest, pytest-asyncio, pytest-cov |
| Validation | Pydantic 2.x |
| Deployment | Docker, Docker Compose |

---

## Project Structure

```
RioVPN/
├── src/
│   ├── bot/                    # Telegram bot layer
│   │   ├── handlers/           # Command handlers
│   │   │   ├── admin.py        # Admin commands
│   │   │   ├── broadcast.py    # Mass notifications
│   │   │   ├── callback.py     # Callback query handlers
│   │   │   ├── command.py      # User commands (/start, /buy, /my)
│   │   │   ├── export.py       # Data export (CSV)
│   │   │   ├── payment.py      # Payment processing
│   │   │   ├── payments.py     # Payment history
│   │   │   ├── referral.py     # Referral program
│   │   │   ├── renewal.py      # Subscription renewal
│   │   │   ├── tiers.py        # Pricing tiers
│   │   │   └── users.py        # User management
│   │   ├── locales/            # i18n translations
│   │   ├── config.py           # Bot configuration
│   │   ├── i18n.py             # Internationalization
│   │   ├── keyboards.py        # Inline keyboards
│   │   ├── main.py             # Bot entry point
│   │   ├── notifications.py    # User notifications
│   │   └── webhooks.py         # Webhook handlers
│   │
│   ├── core/                   # Core infrastructure
│   │   ├── config.py           # Environment settings
│   │   ├── database.py         # Database connection
│   │   ├── health.py           # Health checks
│   │   └── logging.py          # Logging configuration
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py             # User model
│   │   ├── subscription.py     # Subscription model
│   │   ├── payment.py          # Payment model
│   │   ├── referral.py         # Referral model
│   │   └── settings.py         # Settings model
│   │
│   ├── services/               # Business logic & external APIs
│   │   ├── payment/            # Payment providers
│   │   │   ├── base.py         # Base payment class
│   │   │   ├── cryptomus.py    # Cryptomus API
│   │   │   └── yookassa.py     # YooKassa API
│   │   ├── base.py             # Base service class
│   │   ├── hiddify.py          # Hiddify panel API
│   │   ├── three_xui.py        # 3x-ui panel API
│   │   ├── referral.py         # Referral service
│   │   ├── subscription.py     # Subscription management
│   │   └── tiers.py            # Pricing tiers
│   │
│   ├── utils/                  # Helper utilities
│   │
│   └── workers/                # Background workers
│       ├── jobs.py             # Scheduled jobs
│       ├── main.py             # Worker entry point
│       └── scheduler.py        # APScheduler configuration
│
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest fixtures
│   ├── test_models.py          # Model tests
│   ├── test_services.py        # Service tests
│   ├── test_handlers.py        # Handler tests
│   └── test_integration.py     # Integration tests
│
├── migrations/                 # Alembic migrations
│   └── versions/
│
├── scripts/                    # Utility scripts
│   ├── compile_translations.py
│   └── test.py
│
├── .env.example                # Environment template
├── .flake8                     # Flake8 configuration
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Docker Compose config
├── Dockerfile                  # Bot Docker image
├── Dockerfile.worker           # Worker Docker image
├── pyproject.toml              # Tool configurations (black, mypy, ruff)
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
├── spec.md                     # Detailed specification (Russian)
├── TESTING.md                  # Testing guide
├── DEPLOYMENT.md               # Deployment guide
├── CI_CD.md                    # CI/CD documentation
├── PROXY_GUIDE.md              # Proxy setup guide
└── README.md                   # Quick start guide
```

---

## Building and Running

### Prerequisites

- Python 3.11 or higher
- SQLite (built-in) or PostgreSQL 15+ (production)
- Docker and Docker Compose (optional, for containerized deployment)

### Quick Start

1. **Clone and setup environment:**
   ```bash
   git clone https://github.com/yourusername/riovpn.git
   cd riovpn
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize database:**
   ```bash
   python -m migrations upgrade head
   ```

4. **Run the bot:**
   ```bash
   python -m src.bot.main
   ```

5. **Run the background worker (optional - bot includes scheduler):**
   ```bash
   python -m src.workers.main
   ```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop all services
docker-compose down
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v

# Run via script
python scripts/test.py --coverage
```

### Database Migrations

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Create a new migration
python -m migrations revision --autogenerate -m "Description"

# Apply migrations
python -m migrations upgrade head

# Rollback one migration
python -m migrations downgrade -1
```

---

## Configuration

### Environment Variables

See `.env.example` for all required variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Telegram bot token from @BotFather |
| `PANEL_3XUI_URL` | ✅ | 3x-ui panel URL (e.g., `http://ru-vps:2096`) |
| `PANEL_3XUI_USER` | ✅ | 3x-ui admin username |
| `PANEL_3XUI_PASS` | ✅ | 3x-ui admin password |
| `INBOUND_RU_TAG` | ✅ | 3x-ui inbound tag for RU clients |
| `SNI_RU` | ✅ | SNI domain for Reality protocol |
| `PUBLIC_KEY_RU` | ✅ | Reality public key |
| `SHORT_ID_RU` | ✅ | Reality short ID |
| `SERVER_ADDRESS_RU` | ✅ | Russian server IP/domain |
| `SERVER_PORT_RU` | ✅ | Russian server port |
| `PANEL_HIDDIFY_URL` | ✅ | Hiddify panel URL |
| `PANEL_HIDDIFY_API_KEY` | ✅ | Hiddify admin API key |
| `CRYPTOMUS_API_KEY` | ❌ | Cryptomus payment API key |
| `YOOKASSA_SHOP_ID` | ❌ | YooKassa shop ID |
| `YOOKASSA_SECRET_KEY` | ❌ | YooKassa secret key |
| `ADMIN_TELEGRAM_ID` | ✅ | Admin Telegram ID for admin commands |
| `DATABASE_URL` | ✅ | Database connection string |
| `DEFAULT_TRAFFIC_LIMIT_RU` | ❌ | Default RU traffic limit in bytes (empty = unlimited) |
| `DEFAULT_TRAFFIC_LIMIT_EU` | ❌ | Default EU traffic limit in bytes (empty = unlimited) |
| `PROXY_MODE` | ❌ | Proxy mode: `direct`, `socks5`, `http`, `ssh_tunnel` |
| `PROXY_URL` | ❌ | Proxy URL (e.g., `socks5://127.0.0.1:10808`) |
| `PROXY_LOGIN` | ❌ | Proxy authentication login |
| `PROXY_PASSWORD` | ❌ | Proxy authentication password |

### Proxy Configuration

For regions where Telegram is blocked, configure proxy settings:

```bash
# Direct connection (no proxy)
PROXY_MODE=direct

# SOCKS5 proxy (e.g., local 3x-ui inbound)
PROXY_MODE=socks5
PROXY_URL=socks5://127.0.0.1:10808

# HTTP proxy
PROXY_MODE=http
PROXY_URL=http://127.0.0.1:8080

# SSH tunnel mode
PROXY_MODE=ssh_tunnel
PROXY_URL=socks5://127.0.0.1:10808
```

See `PROXY_GUIDE.md` for detailed setup instructions.

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
├── status (Enum: 'pending', 'paid', 'failed', 'refunded')
├── external_id (String) - Payment gateway ID
├── created_at (DateTime)
└── updated_at (DateTime)

Referral
├── id (Integer, PK)
├── referrer_id (FK -> User.telegram_id)
├── referred_id (FK -> User.telegram_id)
├── bonus_amount (Float)
└── created_at (DateTime)

Settings
├── key (String, PK)
├── value (Text)
└── updated_at (DateTime)
```

---

## Bot Commands

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and main menu |
| `/buy` | Purchase new subscription |
| `/my` | View current subscription status |
| `/renew` | Renew existing subscription |
| `/referral` | Referral program information |
| `/support` | Contact support |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Admin panel |
| `/stats` | Sales and traffic statistics |
| `/analytics` | Advanced analytics |
| `/users [limit]` | List users |
| `/search <id>` | Search user by ID |
| `/userhistory <id>` | User history |
| `/payments [limit] [status]` | Payment history |
| `/revenue` | Revenue statistics |
| `/broadcast` | Send message to all users |
| `/export [type]` | Export data to CSV |
| `/suspend <id>` | Suspend user subscription |
| `/grant <id> [type] [days]` | Manually grant subscription |

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

### Payment Gateways

| Provider | Type | Configuration |
|----------|------|---------------|
| Cryptomus | Cryptocurrency | `CRYPTOMUS_API_KEY` |
| YooKassa | Cards (RUB) | `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` |
| Telegram Stars | In-app | Built-in via aiogram |

---

## Background Worker Tasks

| Task | Frequency | Description |
|------|-----------|-------------|
| `check_expiring_subscriptions` | Hourly | Check subscriptions expiring soon |
| `sync_traffic` | Daily (03:00 UTC) | Sync traffic usage from panels |
| `send_reminders` | Daily | Send expiry reminders (3 days before) |
| `check_traffic_warnings` | Daily | Warn users about low traffic |
| `process_webhooks` | Async | Handle payment gateway callbacks |

---

## Development Conventions

### Code Style

- **Type Hints:** Required for all function signatures
- **Docstrings:** Google style for all public functions and classes
- **Async:** All I/O operations must be async (HTTP, DB, file system)
- **Error Handling:** Use custom exceptions with proper logging
- **Logging:** Use `logging` module, not `print()`

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
- Fixtures in `tests/conftest.py`

### Security Rules

- Never hardcode secrets - use environment variables only
- Admin commands restricted by Telegram ID whitelist
- All API calls to panels use retry logic (tenacity)
- Input validation via Pydantic models
- Proper error logging without exposing sensitive data

### Tool Configuration

| Tool | Config File | Purpose |
|------|-------------|---------|
| Black | `pyproject.toml` | Code formatting (line-length: 127) |
| isort | `pyproject.toml` | Import sorting (black profile) |
| mypy | `pyproject.toml` | Type checking |
| ruff | `pyproject.toml` | Linting (E, W, F, I, B, C4, UP) |
| pytest | `pytest.ini` | Testing |
| coverage | `pyproject.toml` | Coverage reporting |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `spec.md` | Detailed project specification (in Russian) |
| `requirements.txt` | Python package dependencies |
| `.env.example` | Environment variable template |
| `pytest.ini` | Pytest configuration |
| `alembic.ini` | Alembic migration configuration |
| `docker-compose.yml` | Docker Compose configuration |
| `pyproject.toml` | Tool configurations (black, mypy, ruff, isort) |
| `TESTING.md` | Testing guide and best practices |
| `DEPLOYMENT.md` | Production deployment guide |
| `CI_CD.md` | CI/CD pipeline documentation |
| `PROXY_GUIDE.md` | Proxy setup for Telegram access |
| `ROADMAP.md` | Development roadmap |
| `.qwen/rules.md` | Development rules and coding standards |

---

## Useful Links

- [aiogram 3.x Documentation](https://docs.aiogram.dev/)
- [SQLAlchemy 2.x Documentation](https://docs.sqlalchemy.org/)
- [3x-ui GitHub](https://github.com/MHSanaei/3x-ui)
- [Hiddify Manager GitHub](https://github.com/hiddify/hiddify-manager)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic 2.x Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
