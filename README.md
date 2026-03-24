# RioVPN — Telegram-бот для продажи VPN-подписок

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI/CD](https://github.com/yourusername/riovpn/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/riovpn/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/yourusername/riovpn/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/riovpn)

**RioVPN** — это полнофункциональный Telegram-бот для автоматизации продажи VPN-подписок с интеграцией платёжных систем (Cryptomus, ЮKassa) и панелей управления (3x-ui, Hiddify-Manager).

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Конфигурация](#-конфигурация)
- [Использование](#-использование)
- [Команды бота](#-команды-бота)
- [Структура проекта](#-структура-проекта)
- [Разработка](#-разработка)
- [Тестирование](#-тестирование)
- [Развёртывание](#-развёртывание)
- [API панелей](#-api-панелей)
- [Технологии](#-технологии)
- [Лицензия](#-лицензия)

---

## ✨ Возможности

### Для пользователей

- 🛒 **Покупка подписок** — выбор типа (RU/EU) и срока (1/3/6/12 месяцев)
- 💎 **Тарифные планы** — Базовый, Премиум, Безлимитный
- 💳 **Оплата онлайн** — Cryptomus (криптовалюта), ЮKassa (карты РФ)
- 🔄 **Продление** — автоматическое продление подписки
- 🎁 **Реферальная программа** — 10% бонус за каждого друга
- 📊 **Статистика** — отслеживание трафика и срока действия
- 🔔 **Уведомления** — напоминания об окончании подписки

### Для администраторов

- 📈 **Статистика** — выручка, пользователи, подписки
- 👥 **Управление пользователями** — поиск, просмотр истории
- 💰 **История платежей** — фильтрация, экспорт в CSV
- 📢 **Рассылки** — массовые уведомления пользователей
- 📊 **Аналитика** — подробные отчёты по метрикам
- ⚙️ **Управление подписками** — выдача, блокировка, продление

### Технические возможности

- 🔄 **Автоматизация** — фоновые задачи (APScheduler)
- 📡 **Интеграции** — 3x-ui, Hiddify-Manager
- 💾 **Базы данных** — SQLite (dev), PostgreSQL (prod)
- 🐳 **Docker** — готовая конфигурация для развёртывания
- 🌐 **i18n** — поддержка русского и английского языков
- 🏥 **Health checks** — мониторинг состояния системы
- 📝 **Логирование** — структурированные логи

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/riovpn.git
cd riovpn
```

### 2. Настройка окружения

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env (обязательные поля)
# BOT_TOKEN, PANEL_3XUI_*, PANEL_HIDDIFY_*, ADMIN_TELEGRAM_ID
```

### 3. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 4. Инициализация базы данных

```bash
# Применение миграций
python -m migrations upgrade head
```

### 5. Запуск бота

```bash
# Запуск бота
python -m src.bot.main

# Запуск воркера (опционально, если отдельно)
python -m src.workers.main
```

### 6. Запуск через Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot

# Остановка
docker-compose down
```

---

## 📦 Установка

### Системные требования

- Python 3.11 или выше
- SQLite (встроено) или PostgreSQL 15+
- Docker 20.10+ (опционально)

### Зависимости

Основные зависимости указаны в `requirements.txt`:

| Пакет | Версия | Назначение |
|-------|--------|------------|
| aiogram | 3.x | Telegram Bot API |
| SQLAlchemy | 2.x | ORM для работы с БД |
| Alembic | 1.x | Миграции базы данных |
| aiohttp | 3.x | HTTP-клиент для API |
| APScheduler | 4.x | Фоновые задачи |
| Pydantic | 2.x | Валидация данных |
| pytest | 7.x | Тестирование |

---

## ⚙️ Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
# Telegram Bot
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# 3x-ui Panel (RU)
PANEL_3XUI_URL=http://your-ru-server:2096
PANEL_3XUI_USER=admin
PANEL_3XUI_PASS=secure_password
INBOUND_RU_TAG=xhttp-ru
SNI_RU=www.kinopoisk.ru
PUBLIC_KEY_RU=your_public_key_here
SHORT_ID_RU=abcd1234
SERVER_ADDRESS_RU=ru.server.com
SERVER_PORT_RU=8443

# Hiddify Panel (EU)
PANEL_HIDDIFY_URL=https://your-eu-server.com
PANEL_HIDDIFY_API_KEY=your-api-key-here

# Payments
CRYPTOMUS_API_KEY=your_cryptomus_key
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# Admin
ADMIN_TELEGRAM_ID=123456789

# Database
DATABASE_URL=sqlite+aiosqlite:///vpn_bot.db
# Или для PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/riovpn

# Defaults (в байтах, пустое = безлимит)
# DEFAULT_TRAFFIC_LIMIT_RU=10737418240
# DEFAULT_TRAFFIC_LIMIT_EU=21474836480
```

### Описание переменных

| Переменная | Обязательная | Описание |
|------------|--------------|----------|
| `BOT_TOKEN` | ✅ | Токен бота от @BotFather |
| `PANEL_3XUI_URL` | ✅ | URL российской панели 3x-ui |
| `PANEL_3XUI_USER` | ✅ | Логин администратора 3x-ui |
| `PANEL_3XUI_PASS` | ✅ | Пароль администратора 3x-ui |
| `INBOUND_RU_TAG` | ✅ | Тег инбаунда для RU клиентов |
| `SNI_RU` | ✅ | SNI домен для Reality |
| `PUBLIC_KEY_RU` | ✅ | Публичный ключ Reality |
| `SHORT_ID_RU` | ✅ | Short ID для Reality |
| `SERVER_ADDRESS_RU` | ✅ | IP или домен RU сервера |
| `SERVER_PORT_RU` | ✅ | Порт RU сервера |
| `PANEL_HIDDIFY_URL` | ✅ | URL европейской панели Hiddify |
| `PANEL_HIDDIFY_API_KEY` | ✅ | API ключ администратора Hiddify |
| `CRYPTOMUS_API_KEY` | ❌ | API ключ Cryptomus |
| `YOOKASSA_SHOP_ID` | ❌ | ID магазина ЮKassa |
| `YOOKASSA_SECRET_KEY` | ❌ | Секретный ключ ЮKassa |
| `ADMIN_TELEGRAM_ID` | ✅ | Telegram ID администратора |
| `DATABASE_URL` | ✅ | URL подключения к БД |

---

## 💡 Использование

### Команды бота

#### Пользовательские команды

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и главное меню |
| `/buy` | Покупка новой подписки |
| `/my` | Просмотр текущей подписки |
| `/renew` | Продление подписки |
| `/referral` | Реферальная программа |
| `/support` | Связаться с поддержкой |

#### Административные команды

| Команда | Описание |
|---------|----------|
| `/admin` | Панель администратора |
| `/stats` | Статистика проекта |
| `/analytics` | Расширенная аналитика |
| `/users [limit]` | Список пользователей |
| `/search <id>` | Поиск пользователя по ID |
| `/userhistory <id>` | История пользователя |
| `/payments [limit] [status]` | История платежей |
| `/revenue` | Статистика выручки |
| `/broadcast` | Рассылка сообщений |
| `/export [type]` | Экспорт данных (CSV) |
| `/suspend <id>` | Блокировка подписки |
| `/grant <id> [type] [days]` | Выдача подписки |

### Примеры использования

#### Покупка подписки

1. Отправьте `/buy` или нажмите «🛒 Купить подписку»
2. Выберите тип: Россия (RU) или Европа (EU)
3. Выберите срок: 1, 3, 6 или 12 месяцев
4. Выберите тариф: Базовый, Премиум, Безлимитный
5. Выберите способ оплаты: Cryptomus или ЮKassa
6. Оплатите по ссылке
7. Получите ссылку для подключения

#### Продление подписки

1. Отправьте `/my` или нажмите «📱 Моя подписка»
2. Нажмите «💳 Продлить»
3. Выберите срок продления
4. Оплатите продление

#### Реферальная программа

1. Отправьте `/referral` или нажмите «🎁 Рефералы»
2. Скопируйте вашу реферальную ссылку
3. Отправьте ссылку друзьям
4. Получите 10% бонус с первого платежа друга (макс. 500 ₽)

---

## 🏗️ Структура проекта

```
RioVPN/
├── src/
│   ├── bot/                    # Telegram бот
│   │   ├── handlers/           # Обработчики команд
│   │   │   ├── admin.py        # Админ-команды
│   │   │   ├── broadcast.py    # Рассылки
│   │   │   ├── callback.py     # Callback-запросы
│   │   │   ├── command.py      # Команды бота
│   │   │   ├── export.py       # Экспорт данных
│   │   │   ├── payment.py      # Платежи
│   │   │   ├── payments.py     # История платежей
│   │   │   ├── referral.py     # Рефералы
│   │   │   ├── renewal.py      # Продление
│   │   │   ├── tiers.py        # Тарифы
│   │   │   ├── users.py        # Управление пользователями
│   │   │   └── __init__.py
│   │   ├── locales/            # Локализация
│   │   │   ├── ru/
│   │   │   └── en/
│   │   ├── config.py           # Конфигурация бота
│   │   ├── i18n.py             # Интернационализация
│   │   ├── keyboards.py        # Inline-клавиатуры
│   │   ├── main.py             # Точка входа бота
│   │   ├── notifications.py    # Уведомления
│   │   └── webhooks.py         # Webhook-обработчики
│   │
│   ├── core/                   # Ядро приложения
│   │   ├── config.py           # Настройки из env
│   │   ├── database.py         # База данных
│   │   ├── health.py           # Health checks
│   │   ├── logging.py          # Логирование
│   │   └── __init__.py
│   │
│   ├── models/                 # SQLAlchemy модели
│   │   ├── user.py             # Пользователи
│   │   ├── subscription.py     # Подписки
│   │   ├── payment.py          # Платежи
│   │   ├── referral.py         # Рефералы
│   │   ├── settings.py         # Настройки
│   │   └── __init__.py
│   │
│   ├── services/               # Внешние сервисы
│   │   ├── payment/            # Платёжные сервисы
│   │   │   ├── base.py         # Базовый класс
│   │   │   ├── cryptomus.py    # Cryptomus API
│   │   │   └── yookassa.py     # ЮKassa API
│   │   ├── base.py             # Базовый сервис
│   │   ├── hiddify.py          # Hiddify API
│   │   ├── three_xui.py        # 3x-ui API
│   │   ├── referral.py         # Реферальный сервис
│   │   ├── subscription.py     # Сервис подписок
│   │   └── tiers.py            # Тарифные планы
│   │
│   ├── utils/                  # Утилиты
│   │   └── __init__.py
│   │
│   └── workers/                # Фоновые задачи
│       ├── jobs.py             # Задачи (expiry, traffic, reminders)
│       ├── main.py             # Точка входа воркера
│       ├── scheduler.py        # Планировщик
│       └── __init__.py
│
├── tests/                      # Тесты
│   ├── conftest.py             # Фикстуры
│   ├── test_models.py          # Тесты моделей
│   ├── test_services.py        # Тесты сервисов
│   ├── test_handlers.py        # Тесты обработчиков
│   └── test_integration.py     # Интеграционные тесты
│
├── migrations/                 # Alembic миграции
│   ├── versions/
│   │   ├── 001_initial.py
│   │   └── 002_referral.py
│   └── env.py
│
├── scripts/                    # Скрипты
│   ├── compile_translations.py # Компиляция локалей
│   └── test.py                 # Запуск тестов
│
├── .env.example                # Пример окружения
├── .gitignore
├── alembic.ini                 # Alembic конфигурация
├── docker-compose.yml          # Docker Compose
├── Dockerfile                  # Docker образ бота
├── Dockerfile.worker           # Docker образ воркера
├── pytest.ini                  # Pytest конфигурация
├── requirements.txt            # Зависимости
├── ROADMAP.md                  # План разработки
├── spec.md                     # Спецификация
├── DEPLOYMENT.md               # Руководство по развёртыванию
├── TESTING.md                  # Руководство по тестированию
└── README.md                   # Этот файл
```

---

## 🧪 Разработка

### Настройка окружения для разработки

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка pre-commit хуков (опционально)
pip install pre-commit
pre-commit install
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src --cov-report=html

# Конкретный файл
pytest tests/test_models.py

# Конкретная функция
pytest tests/test_models.py::TestUserModel::test_create_user

# Через скрипт
python scripts/test.py --coverage
```

### Создание миграций

```bash
# Автоматическая генерация
python -m migrations revision --autogenerate -m "описание"

# Применение миграций
python -m migrations upgrade head

# Откат миграции
python -m migrations downgrade -1
```

### Код-стайл

Проект использует следующие стандарты:

- **Type hints** — аннотации типов для всех функций
- **Docstrings** — Google style для документирования
- **Async/await** — для всех I/O операций
- **Logging** — вместо print()

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Быстрый запуск
pytest

# С покрытием и отчётом
python scripts/test.py --coverage

# Только интеграционные
python scripts/test.py --integration

# Только unit-тесты
python scripts/test.py --unit

# С подробным выводом
python scripts/test.py --verbose
```

### Структура тестов

| Файл | Тестов | Описание |
|------|--------|----------|
| `test_models.py` | 16 | Тесты SQLAlchemy моделей |
| `test_services.py` | 18 | Тесты сервисов (Subscription, Referral, Tiers) |
| `test_handlers.py` | 12 | Тесты обработчиков команд |
| `test_integration.py` | 10 | Интеграционные тесты workflows |

### Покрытие

Целевое покрытие: **80%+**

```bash
# Проверка минимального покрытия
pytest --cov=src --cov-fail-under=80
```

Подробная документация: [TESTING.md](TESTING.md)

---

## ⚙️ CI/CD

### Автоматизация

Проект использует GitHub Actions для автоматизации:

| Событие | Действия |
|---------|----------|
| Push в `main`/`develop` | Запуск тестов, линтинг, сборка Docker |
| Pull Request | Проверка кода, тесты, security scan |
| Каждый понедельник | Проверка зависимостей, backup БД |

### Статусы проверок

- ✅ **Lint passed** — код соответствует стилю
- ✅ **Tests passed** — все тесты проходят
- ✅ **Security passed** — уязвимостей не найдено
- ✅ **Docker build passed** — образ собирается

### Настройка CI/CD

1. Добавьте secrets в repository settings:
   - `CODECOV_TOKEN` — для загрузки coverage отчётов
   - `DEPLOY_TOKEN` — для развёртывания в production

2. Настройте environment `production`:
   - Deployment branches: `main` only
   - Required reviewers: добавьте ревьюеров

Подробная документация: [CI_CD.md](CI_CD.md)

---

## 🚀 Развёртывание

### Docker Compose (рекомендуется)

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Пересборка
docker-compose up -d --build
```

### Сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| `postgres` | 5432 | База данных PostgreSQL |
| `bot` | 8080 | Telegram бот |
| `migrate` | — | Миграции БД (one-time) |

### Production чек-лист

- [ ] Настроить `.env` с реальными данными
- [ ] Использовать PostgreSQL вместо SQLite
- [ ] Настроить HTTPS для webhook
- [ ] Включить логирование в файл
- [ ] Настроить резервное копирование БД
- [ ] Настроить мониторинг (health checks)
- [ ] Ограничить доступ к админ-командам

Подробная инструкция: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🔌 API панелей

### 3x-ui API

**Документация:** [GitHub](https://github.com/MHSanaei/3x-ui/wiki/Configuration#api)

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/panel/api/inbounds/list` | GET | Список инбаундов |
| `/panel/api/inbounds/addClient` | POST | Добавить клиента |
| `/panel/api/inbounds/updateClient` | POST | Обновить клиента |
| `/panel/api/inbounds/delClient` | POST | Удалить клиента |
| `/panel/api/inbounds/getClientTraffic/:email` | GET | Трафик клиента |

**Аутентификация:** Basic Auth (логин/пароль)

### Hiddify API

**Документация:** [GitHub](https://github.com/hiddify/hiddify-manager/wiki/API-Reference)

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v2/admin/user/` | POST | Создать пользователя |
| `/api/v2/admin/user/<uuid>` | GET | Получить пользователя |
| `/api/v2/admin/user/<uuid>` | PUT | Обновить пользователя |
| `/api/v2/admin/user/<uuid>` | DELETE | Удалить пользователя |
| `/api/v2/admin/users/` | GET | Список всех пользователей |

**Аутентификация:** Header `Hiddify-API-Key: <UUID>`

---

## 🛠️ Технологии

| Категория | Технология |
|-----------|------------|
| **Язык** | Python 3.11+ |
| **Bot Framework** | aiogram 3.x |
| **Database** | SQLite / PostgreSQL |
| **ORM** | SQLAlchemy 2.x (async) |
| **Migrations** | Alembic |
| **HTTP Client** | aiohttp |
| **Validation** | Pydantic 2.x |
| **Background Tasks** | APScheduler 4.x |
| **Testing** | pytest, pytest-asyncio |
| **Payments** | Cryptomus, YooKassa |
| **VPN Panels** | 3x-ui, Hiddify-Manager |
| **Deployment** | Docker, Docker Compose |

---

## 📄 Лицензия

MIT License — см. файл [LICENSE](LICENSE) для деталей.

---

## 📞 Поддержка

- **Email:** support@riovpn.example
- **Telegram:** @riovpn_support
- **Документация:** [spec.md](spec.md), [ROADMAP.md](ROADMAP.md)

---

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) — Telegram Bot API framework
- [3x-ui](https://github.com/MHSanaei/3x-ui) — Панель управления Xray
- [Hiddify-Manager](https://github.com/hiddify/hiddify-manager) — Панель управления VPN

---

## 📈 Статус проекта

**Версия:** 1.0.0  
**Статус:** ✅ Готово к продакшену

Все 6 фаз разработки завершены:
- ✅ Phase 1: MVP
- ✅ Phase 2: Платёжные интеграции
- ✅ Phase 3: Управление подписками
- ✅ Phase 4: Админ-панель и аналитика
- ✅ Phase 5: Масштабирование
- ✅ Phase 6: Расширенные функции
