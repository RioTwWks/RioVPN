# Telegram VPN Subscription Bot

## Быстрый старт
```bash
cp .env.example .env
# Заполните .env
docker-compose up -d
```

## Структура
- `src/bot/` — handlers, keyboards, middlewares
- `src/services/` — API клиенты (3x-ui, Hiddify, Payments)
- `src/models/` — SQLAlchemy модели
- `src/workers/` — фоновые задачи

## Документация
- [Спецификация](spec.md)
- [Правила](.qwen/rules.md)
- [Workflow](.qwen/workflows.json)
- [Troubleshooting](.qwen/troubleshooting.md)