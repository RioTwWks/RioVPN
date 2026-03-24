# RioVPN Development Roadmap

## Phase 1: MVP (Minimum Viable Product) 🎯

**Goal:** Core functionality with manual payment confirmation

### Tasks

- [x] **Project Setup**
  - [x] Initialize project structure (`src/bot/`, `src/services/`, `src/models/`, `src/workers/`)
  - [x] Configure SQLAlchemy async with SQLite
  - [x] Setup Alembic migrations
  - [x] Configure logging

- [x] **Database Models**
  - [x] `User` model (telegram_id, username, created_at)
  - [x] `Subscription` model (type, status, dates, traffic, panel_uuid, link)
  - [x] `Payment` model (amount, status, external_id)
  - [x] `Settings` table (key-value config storage)

- [x] **Telegram Bot Core**
  - [x] `/start` command - welcome message + menu
  - [x] `/buy` command - subscription type selection (RU/EU)
  - [x] `/my` command - view current subscription
  - [x] Inline keyboards for navigation
  - [x] Callback query handlers

- [x] **Panel Integrations**
  - [x] 3x-ui API client (async aiohttp)
    - [x] Authentication (Basic Auth)
    - [x] `addClient` method
    - [x] `delClient` method
    - [x] `getClientTraffic` method
  - [x] Hiddify API client (async aiohttp)
    - [x] Authentication (API Key header)
    - [x] `create_user` method
    - [x] `get_user` method
    - [x] `delete_user` method

- [x] **Subscription Logic**
  - [x] vless:// link generation for RU (template-based)
  - [x] Link parsing for EU (from Hiddify response)
  - [x] Database persistence on creation

- [x] **Admin Manual Payment**
  - [x] `/admin` - admin panel
  - [x] `/stats` - view statistics
  - [x] `/suspend <id>` - suspend subscription
  - [x] `/grant <id> [type] [days]` - grant free subscription

**Deliverable:** ✅ Working bot with instant subscription activation

---

## Phase 2: Payment Integrations 💳

**Goal:** Automated payment processing

### Tasks

- [ ] **Payment Gateway Abstraction**
  - [ ] Base `PaymentService` class
  - [ ] Payment provider interface
  - [ ] Webhook handler base class

- [ ] **Cryptomus Integration**
  - [ ] Payment creation API
  - [ ] Webhook endpoint for callbacks
  - [ ] Payment status verification
  - [ ] Crypto payment support (USDT, BTC, etc.)

- [ ] **YooKassa Integration**
  - [ ] Payment creation API
  - [ ] Webhook endpoint
  - [ ] Payment confirmation handling
  - [ ] RUB payment support

- [ ] **Telegram Stars** (optional)
  - [ ] Invoice creation
  - [ ] Pre-checkout query handler
  - [ ] Success handler

- [ ] **Payment Flow**
  - [ ] Automatic subscription activation on payment
  - [ ] Payment retry logic
  - [ ] Refund handling (admin command)

- [ ] **Security**
  - [ ] Webhook signature verification
  - [ ] Idempotency checks
  - [ ] Payment amount validation

**Deliverable:** Fully automated payment processing

---

## Phase 3: Subscription Management 📅

**Goal:** Lifecycle automation

### Tasks

- [ ] **Background Worker Setup**
  - [ ] APScheduler configuration
  - [ ] Async job executor
  - [ ] Error handling & retry

- [ ] **Expiry Management**
  - [ ] Hourly subscription expiry check
  - [ ] Auto-block on expiry (panel API call)
  - [ ] Status update in database

- [ ] **Traffic Monitoring**
  - [ ] Daily traffic sync job (3x-ui API)
  - [ ] Daily traffic sync job (Hiddify API)
  - [ ] Auto-block on traffic limit exceeded
  - [ ] Traffic reset on renewal

- [ ] **Notifications**
  - [ ] Reminder 3 days before expiry
  - [ ] Reminder 1 day before expiry
  - [ ] Expiry notification
  - [ ] Traffic limit warning (80% used)

- [ ] **Renewal Flow**
  - [ ] `/renew` command with payment
  - [ ] Extend expiry date in DB
  - [ ] Update panel via API
  - [ ] Payment for renewal period

- [ ] **Grace Period** (optional)
  - [ ] 24-hour grace after expiry
  - [ ] Reduced speed/traffic during grace

**Deliverable:** Automated subscription lifecycle management

---

## Phase 4: Admin Panel & Analytics 📊

**Goal:** Management tools and insights

### Tasks

- [ ] **Admin Commands**
  - [ ] `/broadcast` - mass notification to users
  - [ ] `/users list` - all users with filters
  - [ ] `/payments list` - payment history

- [ ] **Analytics Dashboard** (inline or web)
  - [ ] Total users (active/expired)
  - [ ] Revenue by period
  - [ ] Popular subscription types
  - [ ] Traffic usage statistics
  - [ ] Conversion funnel

- [ ] **User Management**
  - [ ] Search user by telegram_id
  - [ ] View user subscription history
  - [ ] Manual traffic reset
  - [ ] Extend subscription manually

- [ ] **Logging & Audit**
  - [ ] Admin action logging
  - [ ] Payment audit trail
  - [ ] Error tracking (Sentry integration)

**Deliverable:** Complete admin toolkit

---

## Phase 5: Scaling & Production 🚀

**Goal:** Production-ready deployment

### Tasks

- [ ] **Database Migration**
  - [ ] PostgreSQL setup
  - [ ] Migration from SQLite (data export/import)
  - [ ] Connection pooling configuration
  - [ ] Read replicas (optional)

- [ ] **Dockerization**
  - [ ] Dockerfile for bot
  - [ ] Dockerfile for worker
  - [ ] docker-compose.yml (bot, worker, postgres)
  - [ ] Health checks
  - [ ] Volume mounts for logs

- [ ] **High Availability**
  - [ ] Graceful shutdown handling
  - [ ] Job locking (prevent duplicate workers)
  - [ ] Database connection retry
  - [ ] API rate limiting

- [ ] **Monitoring**
  - [ ] Prometheus metrics endpoint
  - [ ] Grafana dashboards
  - [ ] Alert rules (payment failures, API errors)
  - [ ] Uptime monitoring

- [ ] **CI/CD**
  - [ ] GitHub Actions workflow
  - [ ] Automated tests on PR
  - [ ] Auto-deploy on merge
  - [ ] Rollback strategy

- [ ] **Documentation**
  - [ ] API documentation
  - [ ] Deployment guide
  - [ ] Troubleshooting runbook
  - [ ] User FAQ

**Deliverable:** Production deployment ready

---

## Phase 6: Advanced Features ⭐ (Future)

**Goal:** Enhanced user experience

### Potential Features

- [ ] **Referral Program**
  - [ ] `/referral` command with unique link
  - [ ] Referral code tracking
  - [ ] Bonus for referrer (discount/free days)
  - [ ] Multi-level referrals (optional)

- [ ] **Multi-Language Support**
  - [ ] i18n setup (gettext)
  - [ ] Russian / English locales
  - [ ] Language selection command

- [ ] **Subscription Tiers**
  - [ ] Basic / Premium / Unlimited plans
  - [ ] Different traffic limits per tier
  - [ ] Different server locations per tier

- [ ] **Multi-Server Support**
  - [ ] Load balancing across servers
  - [ ] Auto-select least loaded server
  - [ ] Server health monitoring

- [ ] **Web Admin Panel**
  - [ ] React/Vue dashboard
  - [ ] Real-time statistics
  - [ ] User management UI
  - [ ] Payment management

- [ ] **API for Resellers**
  - [ ] REST API for subscription management
  - [ ] API key authentication
  - [ ] Rate limiting
  - [ ] Documentation (OpenAPI/Swagger)

---

## Timeline Estimate

| Phase | Duration | Priority |
|-------|----------|----------|
| Phase 1: MVP | **✅ Complete** | 🔴 Critical |
| Phase 2: Payments | 1-2 weeks | 🔴 Critical |
| Phase 3: Subscription Mgmt | 1-2 weeks | 🟠 High |
| Phase 4: Admin & Analytics | 1 week | 🟠 High |
| Phase 5: Scaling | 1-2 weeks | 🟡 Medium |
| Phase 6: Advanced | 4+ weeks | 🟢 Low |

**Total MVP:** ✅ Done
**Full Release:** 6-8 weeks remaining

---

## Current Status

**Active Phase:** Phase 2 (Payment Integrations)

**Completed:**
- [x] Project specification
- [x] Requirements definition
- [x] Architecture design
- [x] Core infrastructure setup
- [x] Database models (User, Subscription, Payment, Settings)
- [x] Panel integrations (3x-ui, Hiddify)
- [x] Subscription service with vless:// link generation
- [x] Telegram bot with all MVP commands
- [x] Admin panel with stats, suspend, grant commands
- [x] Alembic migrations configured

**In Progress:**
- [ ] Phase 2: Payment gateway integrations

**Next Milestone:** Cryptomus payment integration
