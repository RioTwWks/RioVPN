# Telegram VPN Subscription Bot

## Quick Start

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python -m migrations upgrade head

# Start the bot
python -m src.bot.main
```

## Project Structure

```
src/
├── bot/           # handlers, keyboards, middlewares
│   ├── handlers/  # command, callback, admin handlers
│   ├── config.py  # bot configuration
│   ├── keyboards.py
│   └── main.py    # entry point
├── core/          # config, database, logging
├── services/      # API clients (3x-ui, Hiddify, Payments)
├── models/        # SQLAlchemy models
├── utils/         # helpers, validators
└── workers/       # background tasks
```

## Documentation

- [Specification](spec.md)
- [Roadmap](ROADMAP.md)
- [Development Rules](.qwen/rules.md)
- [Troubleshooting](.qwen/troubleshooting.md)

## Available Commands

**User Commands:**
- `/start` - Welcome message and main menu
- `/buy` - Purchase subscription
- `/my` - View current subscription
- `/renew` - Renew subscription
- `/support` - Contact support

**Admin Commands:**
- `/admin` - Admin panel
- `/stats` - Statistics
- `/suspend <id>` - Suspend subscription
- `/grant <id> [type] [days]` - Grant free subscription

## Configuration

See `.env.example` for all required variables. Key settings:

- `BOT_TOKEN` - Telegram bot token
- `PANEL_3XUI_*` - 3x-ui panel configuration (RU)
- `PANEL_HIDDIFY_*` - Hiddify panel configuration (EU)
- `ADMIN_TELEGRAM_ID` - Admin Telegram ID for admin access

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run test script
python scripts/test.py --coverage

# Create database migration
python -m migrations revision --autogenerate -m "description"

# Apply migrations
python -m migrations upgrade head
```

## Testing

See [TESTING.md](TESTING.md) for detailed testing guide.

```bash
# Run all tests
pytest

# Run with coverage
python scripts/test.py --coverage

# Run integration tests
python scripts/test.py --integration
```