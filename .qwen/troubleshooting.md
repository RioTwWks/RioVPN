# Руководство по устранению неполадок

## 🔍 Оглавление

1. [Проблемы с запуском бота](#1-проблемы-с-запуском-бота)
2. [Ошибки базы данных](#2-ошибки-базы-данных)
3. [Проблемы интеграции с 3x-ui](#3-проблемы-интеграции-с-3x-ui)
4. [Проблемы интеграции с Hiddify](#4-проблемы-интеграции-с-hiddify)
5. [Ошибки платежей](#5-ошибки-платежей)
6. [Проблемы фоновых задач](#6-проблемы-фоновых-задач)
7. [Docker и развёртывание](#7-docker-и-развёртывание)
8. [Безопасность и конфигурация](#8-безопасность-и-конфигурация)
9. [Производительность](#9-производительность)
10. [Чек-лист диагностики](#10-чек-лист-диагностики)

---

## 1. Проблемы с запуском бота

### 1.1. Бот не запускается

| Симптом | Возможная причина | Решение |
|---------|-------------------|---------|
| `ModuleNotFoundError` | Не установлены зависимости | `pip install -r requirements.txt` |
| `TokenError` | Неверный BOT_TOKEN | Проверьте `.env`, убедитесь что токен скопирован полностью |
| `ImportError` | Неправильная структура проекта | Убедитесь что запускаете из корня проекта |
| `SyntaxError` | Python < 3.11 | Обновите Python: `python --version` |

**Диагностика:**
```bash
# Проверка версии Python
python --version  # должно быть 3.11+

# Проверка установленных пакетов
pip list | grep -E "aiogram|sqlalchemy|aiohttp"

# Запуск с подробным логом
python -m src.bot.main --log-level DEBUG
```

### 1.2. Бот не отвечает на команды

| Симптом | Возможная причина | Решение |
|---------|-------------------|---------|
| Команды не работают | Бот не зарегистрировал handlers | Проверьте `router.include_router()` в main.py |
| Timeout при ответе | Проблемы с интернетом | Проверьте доступность API Telegram |
| Сообщения не приходят | Webhook не настроен | Используйте polling для разработки |

**Проверка:**
```python
# test_bot.py
import asyncio
from aiogram import Bot

async def test():
    bot = Bot(token="YOUR_TOKEN")
    me = await bot.get_me()
    print(f"Bot username: @{me.username}")
    await bot.close()

asyncio.run(test())
```

### 1.3. Ошибки aiogram 3.x

```python
# ❌ ОШИБКА: aiogram 2.x синтаксис
@bot.message_handler(commands=['start'])
async def cmd_start(message: Message):
    ...

# ✅ ПРАВИЛЬНО: aiogram 3.x
from aiogram import Router, F
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    ...
```

---

## 2. Ошибки базы данных

### 2.1. SQLAlchemy async ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `InvalidRequestError: Async session required` | Используется sync сессия | Замените `Session` на `AsyncSession` |
| `OperationalError: no such table` | Таблицы не созданы | Запустите `await init_db()` или Alembic миграцию |
| `PendingRollbackError` | Сессия в ошибочном состоянии | Используйте `async with session.begin()` |

**Правильный паттерн:**
```python
# ✅ ПРАВИЛЬНО
async with async_session_maker() as session:
    async with session.begin():
        user = User(telegram_id=123)
        session.add(user)
        await session.commit()

# ❌ НЕПРАВИЛЬНО
session = Session()  # sync!
user = User(telegram_id=123)
session.add(user)
session.commit()  # blocking!
```

### 2.2. Проблемы с SQLite

| Симптом | Решение |
|---------|---------|
| `database is locked` | Убедитесь что нет concurrent writes, используйте `check_same_thread=False` |
| Медленные запросы | Добавьте индексы: `index=True` на часто используемых полях |
| Миграции не работают | `alembic upgrade head` |

**Конфигурация SQLite для async:**
```python
engine = create_async_engine(
    "sqlite+aiosqlite:///vpn_bot.db",
    connect_args={"check_same_thread": False},
    echo=False
)
```

### 2.3. Alembic миграции

```bash
# Инициализация Alembic
alembic init migrations

# Создать новую миграцию
alembic revision --autogenerate -m "add_subscription_table"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Проверить статус миграций
alembic current
```

**Частые проблемы:**
| Проблема | Решение |
|----------|---------|
| `Target database is not up to date` | `alembic upgrade head` |
| `Multiple head revisions` | `alembic merge -m "merge heads"` |
| Миграция не видит модели | Добавьте `target_metadata = Base.metadata` в `env.py` |

---

## 3. Проблемы интеграции с 3x-ui

### 3.1. Ошибки аутентификации

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `404 Not Found` | 3x-ui использует session cookies, не BasicAuth | Используйте POST на `/login` с CookieJar |
| `401 Unauthorized` | Неверный логин/пароль | Проверьте `PANEL_3XUI_USER` и `PANEL_3XUI_PASS` |
| `Connection refused` | Неверный URL или порт | Проверьте `PANEL_3XUI_URL` (должен включать порт) |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Самоподписанный сертификат | Используйте `ssl=False` в aiohttp |
| `getaddrinfo failed` | DNS не работает через прокси | Настройте SOCKS5 прокси для запросов |

**Диагностика:**
```python
# ✅ ПРАВИЛЬНО: Session-based auth с cookies
import aiohttp
from aiohttp_socks import ProxyConnector
import ssl

async def test_3xui():
    # Создаём CookieJar для сессии
    cookie_jar = aiohttp.CookieJar()
    
    # Создаём прокси коннектор (если нужно)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = ProxyConnector.from_url(
        "socks5://127.0.0.1:10808",
        ssl=ssl_context
    )
    
    async with aiohttp.ClientSession(
        cookie_jar=cookie_jar,
        connector=connector
    ) as session:
        # Логин
        login_data = {
            "username": "your_user",
            "password": "your_pass"
        }
        async with session.post(
            "https://panel-url:port/login",
            json=login_data,
            ssl=False
        ) as resp:
            result = await resp.json()
            print(f"Login: {result.get('success')}")
        
        # API запрос с сессионными куками
        async with session.get(
            "https://panel-url:port/panel/api/inbounds/list",
            ssl=False
        ) as resp:
            print(f"Status: {resp.status}")
            inbounds = await resp.json()
            print(f"Inbounds: {inbounds}")

asyncio.run(test_3xui())
```

**Важно**:
- 3x-ui **не использует** BasicAuth — только session cookies
- После логина куки сохраняются в `CookieJar` и используются автоматически
- Все запросы должны идти через один `ClientSession` с одним `CookieJar`
- Для прокси используйте `ProxyConnector` с `ssl=False`

### 3.2. Ошибки создания клиента

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `json: cannot unmarshal object into Go struct field Inbound.settings of type string` | `settings` передан как object, а не JSON string | Используйте `json.dumps()` для `settings` |
| `Client already exists` | Email уже используется | Используйте уникальный email: `user_<telegram_id>_<timestamp>` |
| `Inbound not found` | Неверный inbound_tag | Поиск работает по `tag` **или** `remark` |
| `Invalid UUID` | Неверный формат UUID | Генерируйте UUID через `uuid.uuid4()` |

**Правильный формат addClient:**
```python
import json

client_config = {
    "id": inbound_id,
    "settings": json.dumps({  # ✅ JSON STRING, не object!
        "clients": [
            {
                "id": uuid,
                "email": email,
                "limitIp": 0,
                "totalGB": traffic_limit or 0,
                "expiryTime": expiry_time or 0,
                "enable": True,
                "tgId": "",
                "subId": "",
            }
        ]
    }),
}

response = await session.post(
    f"{base_url}/panel/api/inbounds/addClient",
    json=client_config,
    ssl=False
)
```

### 3.3. Проблемы с VLESS ссылкой

| Проблема | Решение |
|----------|---------|
| Ссылка не работает | Проверьте все параметры Reality (SNI, public_key, short_id) |
| Клиент не подключается | Убедитесь что порт открыт в фаерволе |
| `invalid link format` | Используйте шаблон из spec.md раздел 5.5 |

**Шаблон VLESS ссылки:**
```
vless://<uuid>@<server>:<port>?encryption=none&flow=xtls-rprx-vision&security=reality&sni=<sni>&fp=chrome&pbk=<public_key>&sid=<short_id>&type=xhttp&path=%2F&mode=auto#<tag>
```

---

## 3a. Проблемы с Proxy (SOCKS5)

### 3a.1. Бот не подключается через прокси

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `ClientOSError: [WinError 64]` | SOCKS5 handshake failed | Проверьте что прокси запущен и принимает соединения |
| `getaddrinfo failed` | DNS не работает | Прокси должен резолвить DNS удалённо (`rdns=True`) |
| `SSL: CERTIFICATE_VERIFY_FAILED` | SSL проверка не проходит | Используйте `ssl=False` или отключите проверку |

**Диагностика:**
```python
# Проверка SOCKS5 прокси
async def test_proxy():
    from aiohttp_socks import ProxyConnector
    import ssl
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = ProxyConnector.from_url(
        "socks5://127.0.0.1:10808",
        ssl=ssl_context
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get("https://api.telegram.org/bot<TOKEN>/getMe") as resp:
            print(f"Status: {resp.status}")
            print(await resp.json())

asyncio.run(test_proxy())
```

**Настройка SSH tunnel для прокси:**
```bash
# PuTTY: Connection → SSH → Tunnels
# - Select: Dynamic (не Local!)
# - Source port: 10808
# - Click: Add

# Или командная строка:
ssh -D 10808 user@server -N
```

### 3a.2. Прокси работает для Telegram, но не для 3x-ui

| Причина | Решение |
|---------|---------|
| Разные ClientSession | Используйте один `ClientSession` с `CookieJar` и `ProxyConnector` |
| SSL проверка включена | Установите `ssl=False` для всех запросов |
| Прокси не для всех запросов | Настройте `BaseService._get_connector()` для использования прокси |

**Правильная конфигурация BaseService:**
```python
class BaseService(ABC):
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        use_proxy: bool = True,      # ✅ Включить прокси
        verify_ssl: bool = False,    # ✅ Отключить SSL проверку
        auth: Optional[aiohttp.BasicAuth] = None,
    ):
        self.use_proxy = use_proxy
        self.verify_ssl = verify_ssl
    
    def _get_connector(self):
        if self.use_proxy:
            from aiohttp_socks import ProxyConnector
            proxy_url = self._get_proxy_url()  # из settings
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ProxyConnector.from_url(proxy_url, ssl=ssl_context)
        return aiohttp.TCPConnector(ssl=False)
```

---

## 4. Проблемы интеграции с Hiddify

### 4.1. Ошибки аутентификации

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `401 Unauthorized` | Неверный API ключ | Проверьте `PANEL_HIDDIFY_API_KEY` |
| `404 Not Found` | Неверный URL или UUID | Проверьте `PANEL_HIDDIFY_URL` (должен заканчиваться на `/`) |
| `SSL Error` | Проблемы с HTTPS | Убедитесь что сертификат валиден |

**Диагностика:**
```bash
# Проверка API ключа
curl -H "Hiddify-API-Key: YOUR_KEY" https://panel-url/api/v2/admin/users/

# Проверка с Python
python -c "
import aiohttp, asyncio, os
async def test():
    headers = {'Hiddify-API-Key': os.getenv('PANEL_HIDDIFY_API_KEY')}
    async with aiohttp.ClientSession(headers=headers) as s:
        async with s.get(os.getenv('PANEL_HIDDIFY_URL') + '/api/v2/admin/users/') as r:
            print(f'Status: {r.status}')
            print(await r.json())
asyncio.run(test())
"
```

### 4.2. Ошибки создания пользователя

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Username already exists` | Дубликат username | Используйте уникальный username: `user_<telegram_id>_<timestamp>` |
| `Invalid expiry_time` | Время в прошлом | Убедитесь что `expiry_time` > текущего времени (Unix timestamp) |
| `Data limit exceeded` | Лимит меньше 0 | Используйте `None` для безлимита или положительное число |

**Правильный формат expiry_time:**
```python
import time
# ✅ Правильно: текущее время + 30 дней в секундах
expiry_time = int(time.time()) + (30 * 24 * 60 * 60)

# ❌ Неправильно: datetime объект
expiry_time = datetime.utcnow() + timedelta(days=30)  # Ошибка!
```

---

## 5. Ошибки платежей

### 5.1. Cryptomus

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Invalid signature` | Неверная подпись | Проверьте алгоритм подписи (MD5 от base64+API_KEY) |
| `Payment not found` | Неверный order_id | Убедитесь что order_id уникален и сохранён в БД |
| `Webhook not received` | Webhook URL недоступен | Проверьте доступность вашего сервера из интернета |

**Проверка подписи:**
```python
import hashlib
import base64
import json

def verify_signature(data: dict, api_key: str, signature: str) -> bool:
    json_data = json.dumps(data)
    b64_data = base64.b64encode(json_data.encode()).decode()
    expected_sign = hashlib.md5((b64_data + api_key).encode()).hexdigest()
    return expected_sign == signature
```

### 5.2. YooKassa

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Shop not found` | Неверный shop_id | Проверьте `YOOKASSA_SHOP_ID` |
| `Invalid secret key` | Неверный секретный ключ | Проверьте `YOOKASSA_SECRET_KEY` в личном кабинете |
| `Amount mismatch` | Сумма не совпадает | Сравнивайте сумму из webhook с суммой в БД |

### 5.3. Telegram Stars

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Pre-checkout failed` | Товар не найден | Убедитесь что `payload` корректен |
| `Payment failed` | Недостаточно звёзд | Проверьте баланс пользователя |

**Обработка pre-checkout:**
```python
@router.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)  # ✅ Обязательно ответить
```

---

## 6. Проблемы фоновых задач

### 6.1. APScheduler ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Job not added` | Scheduler не запущен | Вызовите `scheduler.start()` после инициализации |
| `Task not executed` | Event loop закрыт | Используйте `AsyncIOScheduler` с asyncio |
| `Duplicate job` | Job с таким же ID | Используйте уникальные `job_id` или `replace_existing=True` |

**Правильная инициализация:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=1, id='check_subscriptions')
async def check_subscriptions():
    ...

scheduler.start()  # ✅ После добавления всех jobs
```

### 6.2. Задачи не выполняются

| Симптом | Диагностика | Решение |
|---------|-------------|---------|
| Задачи не запускаются | Проверьте логи scheduler | Убедитесь что event loop активен |
| Задачи выполняются редко | Проверьте timezone | Используйте UTC для всех временных меток |
| Блокировка event loop | Логирование времени выполнения | Разбейте задачу на меньшие части |

**Диагностика:**
```python
import logging
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# Вывод всех запланированных задач
for job in scheduler.get_jobs():
    print(f"Job: {job.id}, Next run: {job.next_run_time}")
```

### 6.3. Синхронизация трафика

| Проблема | Решение |
|----------|---------|
| Трафик не обновляется | Проверьте API вызовы к панелям |
| Трафик сбрасывается | Убедитесь что `traffic_used` не перезаписывается |
| Блокировка не работает | Проверьте условие `traffic_used >= traffic_limit` |

---

## 7. Docker и развёртывание

### 7.1. Бот не запускается в Docker

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `ModuleNotFoundError` | Зависимости не установлены | Добавьте `pip install -r requirements.txt` в Dockerfile |
| `Permission denied` | Неправильные права на файлы | Используйте `chown` или запускайте от root |
| `Container exits immediately` | Ошибка при старте | Проверьте логи: `docker logs <container_id>` |

**Проверка:**
```bash
# Просмотр логов
docker logs vpn-bot

# Интерактивный режим для отладки
docker run -it --entrypoint /bin/bash vpn-bot

# Проверка переменных окружения
docker exec vpn-bot env | grep -E "BOT_|PANEL_"
```

### 7.2. Docker Compose проблемы

| Проблема | Решение |
|----------|---------|
| Сервисы не видят друг друга | Используйте service name как hostname |
| База данных не доступна | Добавьте `depends_on` и healthcheck |
| Тома не монтируются | Проверьте пути в `volumes:` |

**Пример docker-compose.yml:**
```yaml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### 7.3. Проблемы с сетью

| Симптом | Решение |
|---------|---------|
| Webhook не работает | Откройте порт 80/443 в фаерволе |
| API панели недоступны | Проверьте DNS и маршрутизацию |
| Timeout при запросах | Увеличьте timeout в aiohttp ClientSession |

---

## 8. Безопасность и конфигурация

### 8.1. Утечка секретов

| Проблема | Решение |
|----------|---------|
| Секреты в коде | Переместите в переменные окружения |
| `.env` в git | Добавьте в `.gitignore` |
| Логи содержат секреты | Фильтруйте чувствительные данные |

**.gitignore:**
```
.env
.env.local
*.log
__pycache__/
*.pyc
.db
```

### 8.2. Проверка конфигурации

```python
# src/core/config_validator.py
import os
import sys

REQUIRED_ENV = [
    "BOT_TOKEN",
    "PANEL_3XUI_URL",
    "PANEL_3XUI_USER",
    "PANEL_3XUI_PASS",
    "PANEL_HIDDIFY_URL",
    "PANEL_HIDDIFY_API_KEY",
    "ADMIN_TELEGRAM_ID"
]

def validate_config() -> bool:
    missing = [var for var in REQUIRED_ENV if not os.getenv(var)]
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    print("✅ All required environment variables are set")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate_config() else 1)
```

**Запуск проверки:**
```bash
python -m src.core.config_validator
```

---

## 9. Производительность

### 9.1. Медленные запросы

| Проблема | Решение |
|----------|---------|
| Медленные SQL запросы | Добавьте индексы на часто используемые поля |
| Блокирующий I/O | Используйте async/await для всех I/O операций |
| Memory leak | Проверьте утечки с `tracemalloc` |

**Профилирование:**
```python
import tracemalloc

tracemalloc.start()

# ... код ...

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f} MB")
print(f"Peak: {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()
```

### 9.2. Оптимизация базы данных

```sql
-- Добавить индексы
CREATE INDEX idx_subscription_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscription_status ON subscriptions(status);
CREATE INDEX idx_subscription_expiry ON subscriptions(expiry_date);
CREATE INDEX idx_user_telegram_id ON users(telegram_id);
```

### 9.3. Rate limiting API

```python
from aiohttp import ClientSession
from aiohttp_limiter import SemaphoreLimiter

limiter = SemaphoreLimiter(10)  # 10 concurrent requests

async with ClientSession() as session:
    async with limiter:
        async with session.get(url) as resp:
            ...
```

---

## 10. Чек-лист диагностики

### 10.1. Быстрая диагностика

```bash
# 1. Проверка Python версии
python --version  # 3.11+

# 2. Проверка зависимостей
pip check

# 3. Проверка конфигурации
python -m src.core.config_validator

# 4. Проверка подключения к БД
python -c "from src.core.database import engine; print('DB OK')"

# 5. Проверка подключения к Telegram
python -c "from aiogram import Bot; import asyncio; asyncio.run(Bot(token='...').get_me())"

# 6. Проверка 3x-ui API
curl -u user:pass http://panel:2096/panel/api/inbounds/list

# 7. Проверка Hiddify API
curl -H "Hiddify-API-Key: key" https://panel/api/v2/admin/users/

# 8. Проверка логов
tail -f logs/bot.log
```

### 10.2. Чек-лист перед деплоем

| Требование | Статус |
|------------|--------|
| Все секреты в env variables | ☐ |
| `.env` не в git | ☐ |
| Миграции применены | ☐ |
| Логи настроены с ротацией | ☐ |
| Health check endpoint | ☐ |
| Docker image собран | ☐ |
| Webhook URL доступен | ☐ |
| Admin ID настроен | ☐ |
| Тесты проходят | ☐ |

### 10.3. Контакты для поддержки

| Компонент | Документация |
|-----------|-------------|
| aiogram | https://docs.aiogram.dev/ |
| SQLAlchemy | https://docs.sqlalchemy.org/ |
| 3x-ui API | https://github.com/MHSanaei/3x-ui/wiki/Configuration#api |
| Hiddify API | https://github.com/hiddify/hiddify-manager/wiki/API-Reference |
| Cryptomus | https://developers.cryptomus.com/ |
| YooKassa | https://yookassa.ru/developers/ |

---

## 📝 Журнал изменений troubleshooting.md

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0.0 | 2024 | Initial release |