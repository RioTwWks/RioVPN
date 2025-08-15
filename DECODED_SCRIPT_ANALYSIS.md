# RioVPN Telegram Bot - Decoded Script Analysis

## Overview
This document analyzes the decoded `decompressed_code_decoded.py` file, which is a heavily obfuscated Telegram bot launcher for a VPN service called RioVPN.

## Obfuscation Techniques Used

### 1. Variable Name Obfuscation
The original script used random variable names like:
- `Pncgu3BH8BRj = ArithmeticError`
- `L3zigfICm2ax = AssertionError`
- `TKizvQ0BnfYh = function_name`

### 2. String Obfuscation
Strings were obfuscated using XOR encryption with a 40-byte key:
```python
XOR_KEY = [98, 158, 62, 139, 6, 226, 6, 25, 8, 143, 59, 194, 237, 65, 113, 53, 39, 186, 172, 240, 173, 122, 22, 21, 135, 126, 190, 227, 56, 187, 100, 224, 226, 67, 139, 24, 254, 103, 232, 125]
```

### 3. Character Encoding Tricks
Strings were built using character arithmetic:
```python
chr(0b1100 + 0o130) + chr(101) + '\x63' + chr(0b101001 + 0o106)  # Decodes to "utf-8"
```

### 4. Complex Import Statements
Modules were imported using obfuscated paths and getattr calls.

## What the Script Does

### 1. Environment Setup
- **Virtual Environment Creation**: Creates a Python virtual environment if it doesn't exist
- **Dependency Installation**: Installs required packages from `requirements.txt`
- **PostgreSQL Driver**: Installs `psycopg2-binary` for database connectivity

### 2. Database Migration System
- **Alembic Initialization**: Sets up Alembic for database schema migrations
- **Migration Generation**: Automatically generates migrations based on model changes
- **Data Cleanup**: Removes orphaned notifications and referrals before migrations
- **Revision Management**: Handles broken Alembic revisions

### 3. Bot Functionality
- **Telegram Bot**: Main bot instance with webhook support
- **Payment Integration**: Supports multiple payment systems:
  - YooKassa
  - YooMoney
  - CryptoBot
  - Robokassa
  - FreeKassa
- **Subscription Management**: Handles user subscriptions and referrals
- **Notification System**: Sends notifications to users
- **Admin Panel**: Statistics and management features

### 4. Background Tasks
- **Database Backups**: Periodic automated backups
- **Server Health Checks**: Monitors VPN server status
- **Daily Statistics**: Generates daily usage reports
- **Scheduled Jobs**: Uses APScheduler for task scheduling

### 5. Web Interface
- **API Server**: REST API for external integrations
- **Webhook Endpoints**: Payment webhook handlers
- **Subscription Links**: User subscription management

### 6. Security Features
- **Client Code Validation**: Validates bot activation
- **Integrity Check**: Verifies file integrity using a secret key
- **Access Control**: Middleware for user authentication

## Key Components

### Configuration
The bot reads configuration from a `config.py` file including:
- Database connection string
- Payment system settings
- Webhook URLs
- API settings
- Backup schedules

### Database Models
Uses SQLAlchemy with async support for:
- Users
- Subscriptions
- Payments
- Notifications
- Referrals
- Server status

### Payment Systems
Supports multiple payment gateways with webhook validation and transaction processing.

### Development vs Production
- **Development Mode**: Uses polling instead of webhooks
- **Production Mode**: Uses webhooks with aiohttp server

## Security Concerns

1. **Hardcoded Secrets**: The script contains hardcoded access keys
2. **File Integrity**: Uses a simple string comparison for integrity checking
3. **Client Validation**: Basic client code validation system

## Deployment Features

1. **CLI Command Installation**: Installs a `solobot` command for easy management
2. **Auto-restart**: Automatically restarts in virtual environment
3. **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM
4. **Error Recovery**: Handles various error conditions

## Conclusion

This is a sophisticated Telegram bot for a VPN service with comprehensive features including payment processing, user management, and automated maintenance tasks. The obfuscation was likely used to protect the business logic and prevent easy reverse engineering of the payment and subscription systems.

The decoded version (`decompressed_code_fully_decoded.py`) provides a clean, readable implementation that can be used for understanding the bot's functionality or for legitimate development purposes.
