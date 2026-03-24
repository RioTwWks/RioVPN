# RioVPN Deployment Guide

## Overview

This guide covers deployment options for RioVPN, from development to production.

---

## Quick Start (Development)

### Prerequisites

- Python 3.11+
- SQLite (built-in)

### Setup

```bash
# Clone repository
cd RioVPN

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -m migrations upgrade head

# Run the bot
python -m src.bot.main
```

---

## Production Deployment (Docker)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Setup

```bash
# Copy environment file
cp .env.example .env

# Edit configuration
# Required: BOT_TOKEN, PANEL_* settings, ADMIN_TELEGRAM_ID
# Optional: Payment API keys

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| postgres | 5432 | PostgreSQL database |
| bot | 8080 | Telegram bot |
| migrate | - | Database migrations (one-time) |

### Configuration

**Environment Variables:**

```bash
# Telegram
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://riovpn:password@postgres:5432/riovpn
POSTGRES_USER=riovpn
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=riovpn

# 3x-ui Panel
PANEL_3XUI_URL=http://your-ru-server:2096
PANEL_3XUI_USER=admin
PANEL_3XUI_PASS=secure_password

# Hiddify Panel
PANEL_HIDDIFY_URL=https://your-eu-server.com
PANEL_HIDDIFY_API_KEY=your-api-key

# Admin
ADMIN_TELEGRAM_ID=123456789
```

---

## Database Migration

### SQLite to PostgreSQL

1. **Export data from SQLite:**

```python
# export_data.py
import sqlite3
import json

sqlite_conn = sqlite3.connect('vpn_bot.db')
cursor = sqlite_conn.cursor()

# Export tables
tables = ['users', 'subscriptions', 'payments', 'settings']
data = {}

for table in tables:
    cursor.execute(f"SELECT * FROM {table}")
    columns = [desc[0] for desc in cursor.description]
    data[table] = [dict(zip(columns, row)) for row in cursor.fetchall()]

with open('backup.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)
```

2. **Update DATABASE_URL:**

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/riovpn
```

3. **Run migrations:**

```bash
docker-compose up migrate
```

4. **Import data** (if needed, using custom script)

---

## Health Checks

### Manual Health Check

```bash
# Test database connection
python -c "from src.core.health import check_database; import asyncio; print(asyncio.run(check_database()))"

# Full health status
python -c "from src.core.health import get_health_status; import asyncio; h = asyncio.run(get_health_status()); print(h.status)"
```

### Docker Health Check

```bash
docker inspect --format='{{.State.Health.Status}}' riovpn-bot
```

---

## Monitoring

### Logs

```bash
# Bot logs
docker-compose logs -f bot

# Worker logs
docker-compose logs -f worker

# Database logs
docker-compose logs -f postgres
```

### Metrics

Key metrics to monitor:

- **Active subscriptions**: `/stats` command
- **Revenue**: `/revenue` command
- **Failed payments**: Check logs for "Payment failed"
- **Panel connectivity**: Health check endpoint

---

## Backup

### Database Backup

```bash
# PostgreSQL backup
docker exec riovpn-postgres pg_dump -U riovpn riovpn > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i riovpn-postgres psql -U riovpn riovpn < backup_20260324.sql
```

### Configuration Backup

```bash
# Backup .env file
cp .env .env.backup.$(date +%Y%m%d)

# Backup SSL certificates (if using nginx)
tar -czf ssl_backup.tar.gz ./ssl/
```

---

## Troubleshooting

### Bot won't start

1. Check logs: `docker-compose logs bot`
2. Verify `.env` configuration
3. Test database connection: `docker exec riovpn-postgres pg_isready`

### Database migration fails

```bash
# Check current migration
docker-compose run bot python -m migrations current

# Rollback one migration
docker-compose run bot python -m migrations downgrade -1

# Fix and re-run
docker-compose run bot python -m migrations upgrade head
```

### Panel connection errors

1. Verify panel URLs are accessible
2. Check API credentials
3. Test from inside container:
   ```bash
   docker exec -it riovpn-bot wget -qO- http://your-panel:2096
   ```

---

## Security

### Best Practices

1. **Never commit `.env`** - Add to `.gitignore`
2. **Use strong passwords** - For database and panels
3. **Enable HTTPS** - For panel connections
4. **Restrict admin access** - Set `ADMIN_TELEGRAM_ID`
5. **Regular backups** - Daily database backups
6. **Update dependencies** - `pip install --upgrade -r requirements.txt`

### Firewall Rules

Allow only necessary ports:

```bash
# PostgreSQL (if external access needed)
ufw allow 5432/tcp

# Bot webhook (if using webhooks)
ufw allow 8080/tcp
```

---

## Scaling

### Horizontal Scaling

For high load:

1. **Multiple bot instances** - Behind load balancer
2. **Separate worker** - For background tasks
3. **Redis** - For distributed task queue

### Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_expiry ON subscriptions(expiry_date);
CREATE INDEX idx_payments_user ON payments(user_id);
```

---

## Support

For issues:

1. Check logs first
2. Review [troubleshooting.md](.qwen/troubleshooting.md)
3. Contact: support@riovpn.example
