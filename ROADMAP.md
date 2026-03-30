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

- [x] **Payment Gateway Abstraction**
  - [x] Base `PaymentService` class
  - [x] Payment provider interface
  - [x] Webhook handler base class

- [x] **Cryptomus Integration**
  - [x] Payment creation API
  - [x] Webhook endpoint for callbacks
  - [x] Payment status verification
  - [x] Crypto payment support (USDT, BTC, etc.)

- [x] **YooKassa Integration**
  - [x] Payment creation API
  - [x] Webhook endpoint
  - [x] Payment confirmation handling
  - [x] RUB payment support

- [x] **Payment Flow**
  - [x] Automatic subscription activation on payment
  - [x] Payment retry logic
  - [x] Webhook signature verification

- [x] **Bot Integration**
  - [x] Payment selection handlers
  - [x] Payment provider selection
  - [x] Payment URL delivery

**Deliverable:** ✅ Fully automated payment processing

---

## Phase 3: Subscription Management 📅

**Goal:** Lifecycle automation

### Tasks

- [x] **Background Worker Setup**
  - [x] APScheduler configuration
  - [x] Async job executor
  - [x] Error handling & retry

- [x] **Expiry Management**
  - [x] Hourly subscription expiry check
  - [x] Auto-block on expiry (panel API call)
  - [x] Status update in database

- [x] **Traffic Monitoring**
  - [x] Daily traffic sync job (3x-ui API)
  - [x] Daily traffic sync job (Hiddify API)
  - [x] Auto-block on traffic limit exceeded
  - [x] Traffic reset on renewal

- [x] **Notifications**
  - [x] Reminder 3 days before expiry
  - [x] Traffic limit warning (80% used)
  - [x] Payment success notification
  - [x] Subscription blocked notification

- [x] **Renewal Flow**
  - [x] `/renew` command with payment
  - [x] Extend expiry date in DB
  - [x] Update panel via API
  - [x] Payment for renewal period

**Deliverable:** ✅ Automated subscription lifecycle management

---

## Phase 4: Admin Panel & Analytics 📊

**Goal:** Management tools and insights

### Tasks

- [x] **Admin Commands**
  - [x] `/broadcast` - mass notification to users
  - [x] `/users` - list all users with filters
  - [x] `/search <id>` - search user by telegram_id
  - [x] `/userhistory <id>` - view user history
  - [x] `/payments` - payment history with status filter
  - [x] `/revenue` - revenue statistics

- [x] **Analytics Dashboard**
  - [x] Total users (active/expired)
  - [x] Revenue by period (today, month, total)
  - [x] Revenue by payment provider
  - [x] Popular subscription types
  - [x] Payment statistics

- [x] **User Management**
  - [x] Search user by telegram_id
  - [x] View user subscription history
  - [x] User list with registration date

- [x] **Logging & Audit**
  - [x] Admin action logging
  - [x] Payment audit trail

**Deliverable:** ✅ Complete admin toolkit

---

## Phase 5: Scaling & Production 🚀

**Goal:** Production-ready deployment

### Tasks

- [x] **Dockerization**
  - [x] Dockerfile for bot
  - [x] Dockerfile for worker
  - [x] docker-compose.yml (bot, postgres, migrations)
  - [x] Health checks
  - [x] Volume mounts for logs

- [x] **Database Migration**
  - [x] PostgreSQL support (asyncpg)
  - [x] Migration from SQLite documentation
  - [x] Connection pooling configuration

- [x] **High Availability**
  - [x] Graceful shutdown handling
  - [x] Database connection cleanup
  - [x] Signal handling (SIGINT, SIGTERM)

- [x] **Monitoring**
  - [x] Health check module
  - [x] Database connectivity check
  - [x] Panel connection monitoring
  - [x] Subscription health metrics

- [x] **Documentation**
  - [x] Deployment guide (DEPLOYMENT.md)
  - [x] Updated .env.example
  - [x] Backup procedures
  - [x] Troubleshooting guide

**Deliverable:** ✅ Production deployment ready

---

## Phase 6: Advanced Features ⭐ (Future)

**Goal:** Enhanced user experience

### Tasks

- [x] **Referral Program**
  - [x] `/referral` command with unique link
  - [x] Referral code tracking
  - [x] Bonus for referrer (10% discount)
  - [x] Referral statistics

- [x] **Multi-Language Support**
  - [x] i18n setup (gettext)
  - [x] Russian / English locales
  - [x] Translation infrastructure

- [x] **Subscription Tiers**
  - [x] Basic / Premium / Unlimited plans
  - [x] Different traffic limits per tier
  - [x] Different features per tier
  - [x] Tier-based pricing

- [x] **Enhanced Admin**
  - [x] `/export` - Export data to CSV
  - [x] `/analytics` - Advanced analytics dashboard
  - [x] Revenue by provider breakdown
  - [x] User statistics

**Deliverable:** ✅ Enhanced feature set complete
  - [ ] API key authentication
  - [ ] Rate limiting
  - [ ] Documentation (OpenAPI/Swagger)

---

## Timeline Estimate

| Phase | Duration | Priority |
|-------|----------|----------|
| Phase 1: MVP | **✅ Complete** | 🔴 Critical |
| Phase 2: Payments | **✅ Complete** | 🔴 Critical |
| Phase 3: Subscription Mgmt | **✅ Complete** | 🟠 High |
| Phase 4: Admin & Analytics | **✅ Complete** | 🟠 High |
| Phase 5: Scaling & Production | **✅ Complete** | 🟡 Medium |
| Phase 6: Advanced Features | **✅ Complete** | 🟢 Low |

**Total MVP:** ✅ Done
**Full Release:** ✅ Complete - All Features Implemented

---

## Current Status

**Project Status:** ✅ Complete - Production Ready with All Features

**Completed:**
- [x] Project specification
- [x] Requirements definition
- [x] Architecture design
- [x] Core infrastructure setup
- [x] Database models (User, Subscription, Payment, Settings, Referral)
- [x] Panel integrations (3x-ui, Hiddify)
- [x] Subscription service with vless:// link generation
- [x] Telegram bot with all MVP commands
- [x] Admin panel with stats, suspend, grant commands
- [x] Alembic migrations configured
- [x] Payment gateway abstraction layer
- [x] Cryptomus integration (crypto payments)
- [x] YooKassa integration (RUB card payments)
- [x] Automatic subscription activation on payment
- [x] Webhook handlers for payment notifications
- [x] Background scheduler (APScheduler)
- [x] Hourly expiry checks with auto-block
- [x] Daily traffic sync from panels
- [x] Expiry reminders (3 days before)
- [x] Traffic warnings (80% usage)
- [x] Renewal flow with payment integration
- [x] Notification service for user messages
- [x] Broadcast functionality (/broadcast)
- [x] User management (/users, /search, /userhistory)
- [x] Payment history (/payments, /revenue)
- [x] Revenue analytics by provider and period
- [x] Docker configuration (Dockerfile, docker-compose.yml)
- [x] PostgreSQL support (asyncpg)
- [x] Health check module
- [x] Graceful shutdown handling
- [x] Deployment documentation
- [x] Referral program (/referral, tracking, bonuses)
- [x] Multi-language support (i18n, RU/EN)
- [x] Subscription tiers (Basic/Premium/Unlimited)
- [x] Enhanced admin (/export, /analytics)
- [x] Test infrastructure (pytest, fixtures, mocks)
- [x] Model tests (User, Subscription, Payment, Referral)
- [x] Service tests (Subscription, Referral, Tiers)
- [x] Handler tests (Commands, Callbacks, Admin)
- [x] Integration tests (Workflows, Health checks)
- [x] CI/CD pipeline (GitHub Actions)
- [x] Automated testing on push
- [x] Security scanning (bandit, safety)
- [x] Docker build automation
- [x] Scheduled dependency checks
- [x] **Hiddify user creation for RU subscriptions** - Automatic EU user creation for traffic control
- [ ] Deploy to production server
- [ ] Configure monitoring and alerts
- [ ] Set up automated backups
- [ ] Web admin panel
- [ ] Multi-server load balancing
