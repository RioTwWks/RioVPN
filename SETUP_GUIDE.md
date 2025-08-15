# RioVPN Telegram Bot - Setup Guide for Windows

## Prerequisites

1. **Python 3.8+** - Download from https://www.python.org/downloads/
2. **PostgreSQL** - Download from https://www.postgresql.org/download/windows/
3. **Telegram Bot Token** - Get from @BotFather on Telegram

## Installation Steps

### 1. Install PostgreSQL

1. Download PostgreSQL installer from https://www.postgresql.org/download/windows/
2. Run the installer and follow the setup wizard
3. **Important**: Remember the password you set for the `postgres` user
4. Keep the default port (5432)
5. Complete the installation

### 2. Create Database

1. Open Command Prompt as Administrator
2. Navigate to PostgreSQL bin directory (usually `C:\Program Files\PostgreSQL\[version]\bin`)
3. Run: `createdb -U postgres riovpn`
4. Enter the password you set during installation

### 3. Configure the Bot

1. Edit `config.py` and update these values:
   ```python
   # Your Telegram bot token from @BotFather
   API_TOKEN = 'your_actual_bot_token_here'
   
   # Your Telegram user ID (you can get this from @userinfobot)
   ADMIN_ID = 123456789  # Replace with your actual ID
   
   # Database connection (update password)
   DATABASE_URL = 'postgresql+asyncpg://postgres:your_password@localhost/riovpn'
   ```

### 4. Run the Bot

1. Open PowerShell in the project directory
2. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Run the bot:
   ```powershell
   python decompressed_code_fully_decoded.py
   ```

## Troubleshooting

### Database Connection Issues

If you get database connection errors:

1. **Check if PostgreSQL is running**:
   - Open Services (services.msc)
   - Look for "postgresql-x64-[version]" service
   - Make sure it's running

2. **Test database connection**:
   ```powershell
   psql -U postgres -d riovpn
   ```

3. **Verify DATABASE_URL** in `config.py`:
   - Make sure the password matches what you set during PostgreSQL installation
   - Format: `postgresql+asyncpg://postgres:password@localhost/riovpn`

### Bot Token Issues

1. Get a new bot token from @BotFather on Telegram
2. Update `API_TOKEN` in `config.py`
3. Make sure the token is valid and not expired

### Virtual Environment Issues

If the virtual environment doesn't work:

1. Delete the `venv` folder
2. Run the script again - it will recreate the environment
3. Make sure you're using Python 3.8 or higher

## Development Mode

The bot runs in development mode by default (`DEV_MODE = True` in `config.py`). In this mode:

- Uses polling instead of webhooks
- Starts API server on port 8001
- More verbose logging
- No need for external domain/webhook setup

## Production Mode

To run in production mode:

1. Set `DEV_MODE = False` in `config.py`
2. Set up a domain with SSL certificate
3. Update `WEBHOOK_URL` with your domain
4. Configure payment gateways if needed

## Features

This bot includes:

- ✅ User management and subscriptions
- ✅ Payment processing (multiple gateways)
- ✅ Referral system
- ✅ Automated backups
- ✅ Server health monitoring
- ✅ Admin panel
- ✅ API server
- ✅ Web interface

## Support

If you encounter issues:

1. Check the error messages in the console
2. Verify all prerequisites are installed
3. Make sure PostgreSQL is running
4. Check that your bot token is valid
5. Ensure your Telegram ID is correct in the config
