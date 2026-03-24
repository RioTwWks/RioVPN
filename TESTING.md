# RioVPN Testing Guide

## Overview

RioVPN uses pytest for testing with async support via pytest-asyncio.

## Running Tests

### Basic Test Run

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py

# Run specific test function
pytest tests/test_models.py::TestUserModel::test_create_user
```

### Using Test Runner

```bash
# Run all tests
python scripts/test.py

# Run with coverage
python scripts/test.py --coverage

# Run verbose
python scripts/test.py --verbose

# Run integration tests only
python scripts/test.py --integration

# Run unit tests only
python scripts/test.py --unit

# Run specific test
python scripts/test.py tests/test_services.py
```

### Coverage Report

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Check minimum coverage
pytest --cov=src --cov-fail-under=80

# View HTML coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and mocks
├── test_models.py       # Database model tests
├── test_services.py     # Service layer tests
├── test_handlers.py     # Bot handler tests
└── test_integration.py  # Integration/workflow tests
```

## Fixtures

### Database Fixtures

- `db_session` - Async database session
- `db_engine` - Database engine
- `test_db_url` - In-memory SQLite URL

### Model Fixtures

- `user` - Test user (telegram_id: 123456789)
- `subscription` - Test subscription (30 days, 100GB)
- `payment` - Test payment (299 RUB, paid)

### Mock Fixtures

- `mock_bot` - Mocked aiogram Bot
- `mock_callback_query` - Mocked callback query
- `mock_message` - Mocked message
- `mock_three_xui` - Mocked 3x-ui service
- `mock_hiddify` - Mocked Hiddify service
- `mock_env` - Mocked environment variables

## Writing Tests

### Unit Test Example

```python
import pytest
from src.models.user import User

class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        user = User(telegram_id=123456789, username="test")
        db_session.add(user)
        await db_session.commit()
        
        assert user.id is not None
        assert user.telegram_id == 123456789
```

### Integration Test Example

```python
import pytest
from src.services.subscription import SubscriptionService

class TestSubscriptionWorkflow:
    @pytest.mark.asyncio
    async def test_create_subscription(
        self,
        db_session,
        user,
        mock_three_xui,
    ):
        service = SubscriptionService(db_session, mock_three_xui)
        sub = await service.create_subscription(user, "ru", 30)
        
        assert sub.type == "ru"
        mock_three_xui.add_client.assert_called_once()
```

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

async def test_with_mock():
    with patch("src.services.hiddify.HiddifyService") as MockService:
        mock_service = AsyncMock()
        mock_service.create_user = AsyncMock(
            return_value={"uuid": "test-uuid"}
        )
        MockService.return_value = mock_service
        
        # Test code here
```

## Test Categories

### Unit Tests (`test_*.py`)
- Model tests
- Service tests (with mocked dependencies)
- Handler tests (with mocked sessions)

### Integration Tests (`@pytest.mark.integration`)
- Full workflow tests
- Multi-service tests
- End-to-end scenarios

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest --cov=src --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

1. **Use fixtures** - Don't create database objects manually
2. **Mock external services** - Never call real APIs in tests
3. **Test async properly** - Use `@pytest.mark.asyncio`
4. **Clean up resources** - Use async fixtures with cleanup
5. **Name tests clearly** - `test_<action>_<expected_result>`
6. **Keep tests independent** - No test should depend on another
7. **Test edge cases** - Null values, empty lists, errors

## Coverage Goals

| Component | Target |
|-----------|--------|
| Models | 90%+ |
| Services | 85%+ |
| Handlers | 80%+ |
| Overall | 80%+ |

## Troubleshooting

### Test Database Issues

```python
# Ensure in-memory database
@pytest.fixture
def test_db_url():
    return "sqlite+aiosqlite:///:memory:"
```

### Async Fixture Issues

```python
# Use pytest_asyncio.fixture for async fixtures
import pytest_asyncio

@pytest_asyncio.fixture
async def db_session():
    async with session_maker() as session:
        yield session
```

### Mock Not Working

```python
# Patch where used, not where defined
# WRONG: patch("src.services.hiddify.HiddifyService")
# RIGHT: patch("src.bot.handlers.HiddifyService")
```

## Running Tests in Docker

```bash
# Run tests in container
docker-compose run bot pytest

# Run with coverage
docker-compose run bot python scripts/test.py --coverage
```
