# Правила разработки VPN Bot

## 📌 Контекст проекта

**Проект**: Telegram-бот для продажи VPN-подписок (RU/EU)  
**Домен**: vpn, telegram-bot, payments, api-integration  
**Язык**: Python 3.11+  
**Основной фреймворк**: aiogram 3.x

---

## 🏗️ Архитектурные правила

### 1. Структура проекта
```
├── src/
│   ├── bot/           # handlers, keyboards, middlewares
│   ├── core/          # config, database, logging
│   ├── services/      # 3x-ui, hiddify, payments
│   ├── models/        # SQLAlchemy models
│   ├── utils/         # helpers, validators
│   └── workers/       # background tasks
├── tests/
├── docker/
├── migrations/
├── .qwen/
│   ├── mcp.json
│   └── rules.md
└── spec.md
```

### 2. Модульность
- **Каждый сервис изолирован** — 3x-ui, Hiddify, Payments не зависят друг от друга
- **Бот-слой отделён от бизнес-логики** — handlers только вызывают сервисы
- **Конфигурация централизована** — все настройки через `core/config.py`

---

## 💻 Правила кодирования

### 3. Асинхронность
```python
# ✅ ПРАВИЛЬНО
async def create_client(self, telegram_id: int) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            return await resp.json()

# ❌ НЕПРАВИЛЬНО
def create_client(self, telegram_id: int) -> str:
    with requests.post(url, json=data) as resp:  # blocking!
        return resp.json()
```

**Правило**: Все I/O операции (HTTP, DB, FS) должны быть `async/await`

### 4. Типизация
```python
# ✅ ПРАВИЛЬНО
from typing import Optional, List
from datetime import datetime

def get_subscription(user_id: int) -> Optional[Subscription]:
    ...

# ❌ НЕПРАВИЛЬНО
def get_subscription(user_id):  # no type hints
    ...
```

**Правило**: Аннотации типов обязательны для всех функций и методов

### 5. Docstrings (Google Style)
```python
async def create_user_in_hiddify(
    self,
    telegram_id: int,
    expiry_days: int,
    traffic_limit: Optional[int] = None
) -> dict:
    """
    Создаёт пользователя в панели Hiddify-Manager.

    Args:
        telegram_id: Telegram ID пользователя
        expiry_days: Срок действия подписки в днях
        traffic_limit: Лимит трафика в байтах (None = безлимит)

    Returns:
        dict: Данные созданного пользователя (uuid, link, etc.)

    Raises:
        HiddifyAPIError: При ошибке API
        ValidationError: При некорректных входных данных
    """
```

---

## 🔐 Безопасность

### 6. Секреты и конфигурация
```python
# ✅ ПРАВИЛЬНО
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
PANEL_3XUI_PASS = os.getenv("PANEL_3XUI_PASS")

# ❌ НЕПРАВИЛЬНО
BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # hardcoded!
```

**Правило**: 
- Все секреты только из переменных окружения
- Никогда не коммитить `.env` файлы
- Использовать `.env.example` для документации

### 7. Валидация входных данных
```python
# ✅ ПРАВИЛЬНО
from pydantic import BaseModel, Field

class PaymentCallback(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(pattern="^(RUB|USD|EUR)$")
    user_id: int = Field(gt=0)

# ❌ НЕПРАВИЛЬНО
amount = data["amount"]  # no validation
```

### 8. Админ-доступ
```python
# ✅ ПРАВИЛЬНО
async def check_admin(user_id: int) -> bool:
    admin_ids = get_admin_ids_from_config()
    return user_id in admin_ids

# В handler
if not await check_admin(message.from_user.id):
    await message.answer("❌ Доступ запрещён")
    return
```

---

## 🗄️ База данных

### 9. SQLAlchemy модели
```python
# ✅ ПРАВИЛЬНО
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()

# ❌ НЕПРАВИЛЬНО
user = User.query.filter_by(telegram_id=telegram_id).first()  # sync!
```

**Правило**: 
- Использовать `SQLAlchemy 2.x` с async support
- Все сессии через `async with` контекстный менеджер
- Миграции через `Alembic`

### 10. Транзакции
```python
# ✅ ПРАВИЛЬНО
async with session.begin():
    subscription = Subscription(...)
    session.add(subscription)
    await panel_service.create_client(...)  # если ошибка — rollback

# ❌ НЕПРАВИЛЬНО
session.add(subscription)
await session.commit()  # no rollback on error
```

---

## 🔌 API Интеграции

### 11. 3x-ui API
```python
# ✅ ПРАВИЛЬНО
BASE_URL = os.getenv("PANEL_3XUI_URL")
AUTH = aiohttp.BasicAuth(
    login=os.getenv("PANEL_3XUI_USER"),
    password=os.getenv("PANEL_3XUI_PASS")
)

async def get_inbounds(self) -> list:
    async with aiohttp.ClientSession(auth=AUTH) as session:
        async with session.get(f"{BASE_URL}/panel/api/inbounds/list") as resp:
            resp.raise_for_status()
            return await resp.json()

# ❌ НЕПРАВИЛЬНО
requests.get(f"http://{BASE_URL}/...")  # no auth, sync
```

**Эндпоинты**:
| Метод | Эндпоинт | Назначение |
|-------|----------|------------|
| GET | `/panel/api/inbounds/list` | Список инбаундов |
| POST | `/panel/api/inbounds/addClient` | Добавить клиента |
| POST | `/panel/api/inbounds/updateClient` | Обновить клиента |
| POST | `/panel/api/inbounds/delClient` | Удалить клиента |
| GET | `/panel/api/inbounds/getClientTraffic/:email` | Трафик |

### 12. Hiddify API
```python
# ✅ ПРАВИЛЬНО
HEADERS = {"Hiddify-API-Key": os.getenv("PANEL_HIDDIFY_API_KEY")}
BASE_URL = f"{os.getenv('PANEL_HIDDIFY_URL')}/api/v2/"

async def create_user(self, username: str, expiry: int) -> dict:
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.post(
            f"{BASE_URL}admin/user/",
            json={"username": username, "expiry_time": expiry}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()
```

### 13. Retry логика
```python
# ✅ ПРАВИЛЬНО
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def call_panel_api(self, url: str, data: dict) -> dict:
    async with session.post(url, json=data) as resp:
        resp.raise_for_status()
        return await resp.json()
```

**Правило**: Все API вызовы к панелям должны иметь retry логику

---

## ⚠️ Обработка ошибок

### 14. Логирование
```python
# ✅ ПРАВИЛЬНО
import logging
logger = logging.getLogger(__name__)

try:
    await service.create_client(...)
except APIError as e:
    logger.error(f"Failed to create client: {e}", exc_info=True)
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise

# ❌ НЕПРАВИЛЬНО
print("Error occurred")  # no logging
```

**Уровни логирования**:
| Уровень | Когда использовать |
|---------|-------------------|
| INFO | Успешные операции (создание подписки, оплата) |
| WARNING | Предупреждения (мало трафика, скоро истечение) |
| ERROR | Ошибки API, базы данных |
| CRITICAL | Критические сбои (бот не запускается) |

### 15. Пользовательские исключения
```python
# ✅ ПРАВИЛЬНО
class SubscriptionError(Exception):
    pass

class PanelAPIError(SubscriptionError):
    pass

class PaymentError(SubscriptionError):
    pass

# В коде
try:
    await hiddify.create_user(...)
except aiohttp.ClientError as e:
    raise PanelAPIError(f"Hiddify API failed: {e}")
```

---

## 🧪 Тестирование

### 16. Покрытие тестами
```python
# ✅ ПРАВИЛЬНО
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_subscription():
    mock_session = AsyncMock()
    mock_panel = AsyncMock()
    
    service = SubscriptionService(mock_session, mock_panel)
    result = await service.create_subscription(user_id=123, type="ru")
    
    assert result.status == "active"
    mock_panel.create_client.assert_called_once()

# ❌ НЕПРАВИЛЬНО
# Нет тестов для критической логики
```

**Правило**: 
- Критические пути (оплата, создание подписки) должны иметь тесты
- Использовать `pytest-asyncio` для async тестов
- Моки для внешних API

---

## 🔄 Фоновые задачи

### 17. APScheduler / asyncio
```python
# ✅ ПРАВИЛЬНО
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=1)
async def check_expiring_subscriptions():
    async with get_session() as session:
        subs = await get_expiring_soon(session)
        for sub in subs:
            await notify_user(sub.user_id)

scheduler.start()

# ❌ НЕПРАВИЛЬНО
while True:
    time.sleep(3600)  # blocking!
    check_subscriptions()
```

**Задачи воркера**:
| Задача | Частота | Описание |
|--------|---------|----------|
| `check_expiring_subscriptions` | Каждый час | Проверка истекающих подписок |
| `sync_traffic` | Раз в сутки | Синхронизация трафика с панелями |
| `send_reminders` | Каждый день | Уведомления за 3 дня до окончания |
| `process_webhooks` | Асинхронно | Обработка платежных уведомлений |

---

## 📦 Конфигурация

### 18. Переменные окружения
```bash
# .env.example
BOT_TOKEN=
PANEL_3XUI_URL=
PANEL_3XUI_USER=
PANEL_3XUI_PASS=
PANEL_HIDDIFY_URL=
PANEL_HIDDIFY_API_KEY=
INBOUND_RU_TAG=
SNI_RU=
PUBLIC_KEY_RU=
SHORT_ID_RU=
SERVER_ADDRESS_RU=
SERVER_PORT_RU=
DEFAULT_TRAFFIC_LIMIT_RU=
DEFAULT_TRAFFIC_LIMIT_EU=
CRYPTOMUS_API_KEY=
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
ADMIN_TELEGRAM_ID=
DATABASE_URL=sqlite+aiosqlite:///vpn_bot.db
```

### 19. Settings таблица в БД
```python
# Динамические настройки хранятся в БД
class Settings(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime)

# Пример: prices, payment_methods, feature_flags
```

---

## 🚀 Deployment

### 20. Docker
```dockerfile
# ✅ ПРАВИЛЬНО
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY migrations/ ./migrations/

CMD ["python", "-m", "src.bot.main"]

# ❌ НЕПРАВИЛЬНО
FROM python:3.11
COPY . .  # включает .env, .git, etc.
```

### 21. Docker Compose
```yaml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    
  worker:
    build: .
    env_file: .env
    command: python -m src.workers.scheduler
    restart: unless-stopped
```

---

## 📝 Чек-лист перед коммитом

| Требование | Статус |
|------------|--------|
| Type hints для всех функций | ☐ |
| Docstrings в Google style | ☐ |
| Async для всех I/O операций | ☐ |
| Логирование (INFO/ERROR) | ☐ |
| Обработка ошибок с retry | ☐ |
| Секреты в env variables | ☐ |
| Валидация входных данных | ☐ |
| Тесты для критических путей | ☐ |
| Нет hardcoded значений | ☐ |
| Соответствует spec.md | ☐ |

---

## 🎯 Qwen CLI инструкции

При генерации кода всегда:

1. **Сверяться с `spec.md`** — архитектура и модели должны соответствовать
2. **Использовать существующие модели** — не создавать дублирующие структуры
3. **Следовать API документации** — 3x-ui и Hiddify API точно по спецификации
4. **Добавлять error handling** — все внешние вызовы с try/except и логированием
5. **Конфигурация из env/БД** — никаких хардкодов
6. **Модульный дизайн** — разделять bot/services/workers

---

## 📚 Полезные ссылки

| Ресурс | Описание |
|--------|----------|
| [aiogram 3.x docs](https://docs.aiogram.dev/) | Фреймворк для бота |
| [SQLAlchemy 2.x](https://docs.sqlalchemy.org/) | ORM с async support |
| [3x-ui API](https://github.com/MHSanaei/3x-ui/wiki/Configuration#api) | Российская панель |
| [Hiddify API](https://github.com/hiddify/hiddify-manager/wiki/API-Reference) | Европейская панель |
| [APScheduler](https://apscheduler.readthedocs.io/) | Фоновые задачи |
| [Alembic](https://alembic.sqlalchemy.org/) | Миграции БД |