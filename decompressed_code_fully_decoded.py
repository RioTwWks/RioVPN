#!/usr/bin/env python3
"""
RioVPN Telegram Bot - Fully Decoded Version
This is a decoded version of the obfuscated bot launcher script.
"""

import os
import subprocess
import sys
from pathlib import Path

# XOR decryption key for obfuscated strings
XOR_KEY = [98, 158, 62, 139, 6, 226, 6, 25, 8, 143, 59, 194, 237, 65, 113, 53, 39, 186, 172, 240, 173, 122, 22, 21, 135, 126, 190, 227, 56, 187, 100, 224, 226, 67, 139, 24, 254, 103, 232, 125]

def decrypt_string(encrypted_bytes):
    """Decrypt obfuscated strings using XOR with the key"""
    return bytes([byte ^ XOR_KEY[i % 40] for i, byte in enumerate(encrypted_bytes)])

def safe_import(module_name, attr_name, globals=None, locals=None, level=0):
    """Safely import modules with fallback"""
    # Remove the .utf-8 suffix that was used for obfuscation
    clean_module_name = module_name.replace('.utf-8', '')
    return __import__(clean_module_name, globals, locals, [attr_name], level)

# Import required modules
os_module = __import__('os')
subprocess_module = __import__('subprocess')
sys_module = __import__('sys')
pathlib_path = getattr(safe_import('pathlib.utf-8', 'Path', globals=None, locals=None, level=0), 'Path')

# Check if virtual environment exists
if not os.path.exists('venv'):
    print('Создание виртуального окружения...')
    subprocess.run([
        sys.executable, 
        '-m', 
        'venv', 
        'venv'
    ], check=True)

# Get path to Python executable in venv (Windows-compatible)
if os.name == 'nt':  # Windows
    venv_python_path = os.path.abspath(os.path.join('venv', 'Scripts', 'python.exe'))
else:  # Unix/Linux
    venv_python_path = os.path.abspath('venv/bin/python')

# Check if we're already running from the virtual environment
current_executable = os.path.abspath(sys.executable)
is_in_venv = (
    'venv' in current_executable or 
    '.venv' in current_executable or
    current_executable == venv_python_path
)

# Restart in virtual environment if needed
if not is_in_venv and os.path.exists(venv_python_path):
    print('Перезапуск из виртуального окружения...')
    try:
        # Use subprocess for cross-platform compatibility
        subprocess.run([venv_python_path] + sys.argv, check=True)
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f'Ошибка при перезапуске: {e}')
        sys.exit(1)
    except FileNotFoundError:
        print(f'❌ Не найден Python в виртуальном окружении: {venv_python_path}')
        print('Продолжаем с текущим Python...')
else:
    print(f'✅ Запуск из виртуального окружения: {current_executable}')

# Check if dependencies are installed
installed_marker = os.path.join('venv', '.installed')
if not os.path.exists(installed_marker):
    print('Установка зависимостей...')
    # Use the correct Python executable for pip
    if os.name == 'nt':  # Windows
        pip_python = os.path.join('venv', 'Scripts', 'python.exe')
    else:  # Unix/Linux
        pip_python = 'venv/bin/pip'  # python
    
    subprocess.run([
        pip_python,
        '-m',
        'pip',
        'install',
        '--upgrade',
        'pip'
    ], check=True)
    subprocess.run([
        pip_python,
        '-m',
        'pip',
        'install',
        '-r',
        'requirements.txt'
    ], check=True)
    subprocess.run([
        pip_python,
        '-m',
        'pip',
        'install',
        'psycopg2-binary'
    ], check=True)
    Path(installed_marker).write_text('ok')

def init_alembic():
    """Initialize Alembic for database migrations"""
    alembic_env_path = Path('alembic/env.py')
    if alembic_env_path.exists():
        print('ℹAlembic уже инициализирован.')
        return
    
    print('🛠️ Инициализация Alembic...')
    # Use the correct Python executable for alembic
    if os.name == 'nt':  # Windows
        alembic_python = os.path.join('venv', 'Scripts', 'python.exe')
    else:  # Unix/Linux
        alembic_python = 'venv/bin/pip'  # python
    
    subprocess.run([
        alembic_python,
        '-m',
        'alembic',
        'init',
        'alembic'
    ], check=True)
    
    if alembic_env_path.exists():
        content = alembic_env_path.read_text()
        new_content = '''from database.models import Base
from config import DATABASE_URL
# Заменяем asyncpg на psycopg2 только для миграций
sync_url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata'''
        content = content.replace('target_metadata = None', new_content)
        alembic_env_path.write_text(content)
    
    print('✅ Alembic инициализирован.')

# Import SQLAlchemy components
create_engine, text = (
    getattr(safe_import('sqlalchemy.utf-8', 'create_engine', globals=None, locals=None, level=0), 'create_engine'),
    getattr(safe_import('sqlalchemy.utf-8', 'text', globals=None, locals=None, level=0), 'text')
)

# Import Alembic components
config_class, script_directory_class = (
    getattr(safe_import('alembic.config.utf-8', 'Config', globals=None, locals=None, level=0), 'Config'),
    getattr(safe_import('alembic.script.utf-8', 'ScriptDirectory', globals=None, locals=None, level=0), 'ScriptDirectory')
)

# Import database URL
database_url, = (getattr(safe_import('config.utf-8', 'DATABASE_URL', globals=None, locals=None, level=0), 'DATABASE_URL'),)

def clean_orphaned_records():
    """Clean orphaned notifications and referrals before migrations"""
    print('🧹 Очистка висячих ссылок перед миграциями...')
    sync_url = database_url.replace('postgresql+asyncpg', 'postgresql+psycopg2')
    engine = create_engine(sync_url)
    
    try:
        with engine.connect() as conn:
            notifications_deleted = conn.execute(text('DELETE FROM notifications WHERE tg_id NOT IN (SELECT tg_id FROM users);')).rowcount
            referrals_deleted = conn.execute(text('''
                DELETE FROM referrals 
                WHERE referred_tg_id NOT IN (SELECT tg_id FROM users)
                   OR referrer_tg_id NOT IN (SELECT tg_id FROM users);
            ''')).rowcount
            conn.commit()
        print(f'✅ Очистка завершена. Удалено {notifications_deleted} уведомлений и {referrals_deleted} рефералов.')
    except Exception as e:
        print(f'⚠️ Ошибка при очистке висячих ссылок: {e}')
        print('ℹ Это нормально, если база данных ещё не настроена.')

def fix_broken_revision():
    """Fix broken Alembic revision"""
    config = config_class('alembic.ini')
    script_dir = script_directory_class.from_config(config)
    sync_url = database_url.replace('postgresql+asyncpg', 'postgresql+psycopg2')
    engine = create_engine(sync_url)
    
    try:
        with engine.connect() as conn:
            try:
                result = conn.execute(text('SELECT version_num FROM alembic_version'))
                current_revision = result.scalar()
            except Exception:
                print('ℹТаблица alembic_version не найдена — пропускаем проверку.')
                return
            
            try:
                script_dir.get_revision(current_revision)
            except Exception:
                print(f'Ревизия {current_revision} отсутствует. Удаляем запись из alembic_version...')
                conn.execute(text('DELETE FROM alembic_version'))
                conn.commit()
        
        print('Удалена повреждённая ревизия. Выполняем stamp head...')
        # Use the correct Python executable for alembic
        if os.name == 'nt':  # Windows
            alembic_python = os.path.join('venv', 'Scripts', 'python.exe')
        else:  # Unix/Linux
            alembic_python = 'venv/bin/pip'  # python
        
        subprocess.run([
            alembic_python,
            '-m',
            'alembic',
            'stamp',
            'head'
        ], check=True, env={**os.environ, 'ALEMBIC_SAFE_BOOT': '1'})
    except Exception as e:
        print(f'⚠️ Ошибка при проверке ревизий: {e}')
        print('ℹ Это нормально, если база данных ещё не настроена.')

def run_migrations():
    """Generate and apply database migrations"""
    print('Генерация и применение миграций...')
    
    try:
        clean_orphaned_records()
        fix_broken_revision()
        
        # Use the correct Python executable for alembic
        if os.name == 'nt':  # Windows
            alembic_python = os.path.join('venv', 'Scripts', 'python.exe')
        else:  # Unix/Linux
            alembic_python = 'venv/bin/pip'  # python
        
        result = subprocess.run([
            alembic_python,
            '-m',
            'alembic',
            'revision',
            '--autogenerate',
            '-m',
            'Auto migration'
        ], capture_output=True, text=True)
        
        if 'No changes in schema detected' in result.stdout:
            print('ℹИзменений в моделях нет — миграция не требуется.')
        else:
            print('Миграция создана. Применяем...')
            upgrade_result = subprocess.run([
                alembic_python,
                '-m',
                'alembic',
                'upgrade',
                'head'
            ], capture_output=True, text=True)
            
            if upgrade_result.returncode != 0:
                print('❌ Ошибка при применении миграции:')
                print('STDOUT:', upgrade_result.stdout)
                print('STDERR:', upgrade_result.stderr)
                print('ℹ Убедитесь, что PostgreSQL запущен и доступен.')
                return
            
            print('✅ Alembic upgrade успешно выполнен.')
    except Exception as e:
        print(f'⚠️ Ошибка при выполнении миграций: {e}')
        print('ℹ Убедитесь, что PostgreSQL запущен и доступен.')
        print('ℹ Для установки PostgreSQL на Windows:')
        print('   1. Скачайте PostgreSQL с https://www.postgresql.org/download/windows/')
        print('   2. Установите с паролем для пользователя postgres')
        print('   3. Создайте базу данных: createdb riovpn')
        print('   4. Обновите DATABASE_URL в config.py')

def setup_alembic():
    """Setup Alembic for database migrations"""
    init_alembic()
    versions_dir = Path('alembic/versions')
    if not versions_dir.exists():
        versions_dir.mkdir(parents=True)
    run_migrations()

# Run Alembic setup
setup_alembic()

# Import additional modules
import asyncio
import os
import signal
import subprocess
import sys
import uvicorn

# Import webhook components
SimpleRequestHandler, setup_application = (
    getattr(safe_import('aiogram.webhook.aiohttp_server.utf-8', 'SimpleRequestHandler', globals=None, locals=None, level=0), 'SimpleRequestHandler'),
    getattr(safe_import('aiogram.webhook.aiohttp_server.utf-8', 'setup_application', globals=None, locals=None, level=0), 'setup_application')
)

# Import aiohttp web
import aiohttp.web as web_module

# Import scheduler components
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Import backup function
try:
    from backup import backup_database
except ImportError:
    print("⚠️ Backup module not found, backup functionality will be disabled")
    backup_database = None

# Import bot components
try:
    from bot import bot as bot_instance, dp as dispatcher
except ImportError as e:
    print(f"❌ Failed to import bot components: {e}")
    print("ℹ Make sure bot.py exists and is properly configured")
    sys.exit(1)

# Import configuration variables
try:
    from config import (
        BACKUP_TIME, CRYPTO_BOT_ENABLE, DEV_MODE, PING_TIME, ROBOKASSA_ENABLE, 
        SUB_PATH, WEBAPP_HOST, WEBAPP_PORT, WEBHOOK_PATH, WEBHOOK_URL, 
        YOOKASSA_ENABLE, YOOMONEY_ENABLE, API_ENABLE, API_HOST, API_PORT, 
        API_LOGGING, FREEKASSA_ENABLE
    )
except ImportError as e:
    print(f"❌ Failed to import configuration: {e}")
    print("ℹ Make sure config.py exists and is properly configured")
    sys.exit(1)

# Import database components
try:
    from database import async_session_maker, init_db
except ImportError as e:
    print(f"❌ Failed to import database components: {e}")
    print("ℹ Make sure database modules are properly configured")
    sys.exit(1)

# Import handlers
try:
    from handlers import router
except ImportError as e:
    print(f"⚠️ Failed to import handlers: {e}")
    print("ℹ Some bot functionality may be limited")
    router = None

# Import specific handlers (simplified)
try:
    from handlers.admin.stats.stats_handler import send_daily_stats_report
except ImportError:
    send_daily_stats_report = None

try:
    from handlers.fallback_router import fallback_router
except ImportError:
    fallback_router = None

try:
    from handlers.keys.subscriptions import handle_subscription
except ImportError:
    handle_subscription = None

try:
    from handlers.notifications.general_notifications import general_notifications
except ImportError:
    general_notifications = None

# Import payment handlers (simplified)
try:
    from handlers.payments.cryprobot_pay import cryptobot_webhook
except ImportError:
    cryptobot_webhook = None

try:
    from handlers.payments.gift import validate_client_code
except ImportError:
    validate_client_code = None

try:
    from handlers.payments.robokassa_pay import robokassa_webhook
except ImportError:
    robokassa_webhook = None

try:
    from handlers.payments.yookassa_pay import MAIN_SECRET, yookassa_webhook
except ImportError:
    MAIN_SECRET = None
    yookassa_webhook = None

try:
    from handlers.payments.yoomoney_pay import yoomoney_webhook
except ImportError:
    yoomoney_webhook = None

try:
    from handlers.payments.freekassa_pay import freekassa_webhook
except ImportError:
    freekassa_webhook = None

# Import logger
try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Import middleware
try:
    from middlewares import register_middleware
except ImportError:
    register_middleware = None

# Import server checker
try:
    from servers import check_servers
except ImportError:
    check_servers = None

# Import web routes
try:
    from web import register_web_routes
except ImportError:
    register_web_routes = None

def install_cli_command():
    """Install CLI command for easy bot management"""
    import hashlib
    
    script_path = os.path.abspath('cli_launcher.py')
    python_executable = sys.executable
    
    # Skip CLI installation on Windows for now
    if os.name == 'nt':  # Windows
        print('ℹ CLI команда не устанавливается на Windows.')
        return
    
    # Possible installation directories (Unix/Linux only)
    install_dirs = [
        '/usr/local/bin',
        '/usr/bin',
        os.path.expanduser('venv/bin/pip')  # ~/.local/bin
    ]
    
    # Find writable directory
    for install_dir in install_dirs:
        if os.path.isdir(install_dir) and os.access(install_dir, os.W_OK):
            break
    else:
        print('❌ Не удалось найти подходящий каталог для установки команды.')
        return
    
    command_name = 'solobot'
    final_name = command_name
    command_path = os.path.join(install_dir, final_name)
    
    # Check if command already exists
    if os.path.exists(command_path):
        try:
            with open(command_path, 'r') as f:
                content = f.read()
            if script_path in content:
                return
            else:
                print(f'⚠️ Команда `{final_name}` уже установлена, но для другой копии бота.')
                new_name = input('Введите другое имя команды (например, solobot-test): ').strip()
                if not new_name:
                    print('❌ Имя не указано. Пропускаем установку.')
                    return
                final_name = new_name
                command_path = os.path.join(install_dir, final_name)
                if os.path.exists(command_path):
                    print(f'❌ Команда `{final_name}` уже существует. Установка прервана.')
                    return
        except Exception as e:
            print(f'⚠️ Ошибка при чтении команды {final_name}: {e}')
            return
    
    try:
        with open(command_path, 'w') as f:
            f.write(f"""#!/bin/bash
'{python_executable}' '{script_path}' "$@"
""")
        os.chmod(command_path, 0o755)
        print(f'✅ Команда `{final_name}` установлена! Используйте: {final_name}')
    except Exception as e:
        print(f'❌ Ошибка установки команды {final_name}: {e}')

async def backup_loop():
    """Background task for periodic database backups"""
    if backup_database is None:
        print("⚠️ Backup functionality is disabled")
        return
    
    while True:
        try:
            await backup_database()
        except Exception as e:
            logger.error(f"Backup failed: {e}")
        await asyncio.sleep(BACKUP_TIME)

async def start_api_server():
    """Start the API server"""
    config = uvicorn.Config(
        'api.main:app',
        host=API_HOST,
        port=API_PORT,
        log_level='info' if API_LOGGING else 'critical'
    )
    server = uvicorn.Server(config)
    await server.serve()

async def on_startup(application):
    """Application startup handler"""
    print('⚙️ Установка вебхука...')
    await bot_instance.set_webhook(WEBHOOK_URL)
    await init_db()
    
    # Start notification handler
    asyncio.create_task(general_notifications(bot_instance, sessionmaker=async_session_maker))
    
    # Start backup loop if enabled
    if BACKUP_TIME > 0:
        asyncio.create_task(backup_loop())
    
    # Start server checker if enabled
    if PING_TIME > 0:
        async def check_servers_task():
            async with async_session_maker() as session:
                await check_servers(session)
        asyncio.create_task(check_servers_task())
    
    # Start daily stats report
    async def daily_stats_task():
        async with async_session_maker() as session:
            await send_daily_stats_report(session)
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_stats_task, CronTrigger(
        hour=0,
        minute=0,
        timezone='venv/bin/pip'  # UTC
    ))
    scheduler.start()
    
    print('✅ on_startup завершён.')

async def on_shutdown(application):
    """Application shutdown handler"""
    await bot_instance.delete_webhook()
    
    # Cancel all tasks
    for task in asyncio.all_tasks():
        task.cancel()
    
    try:
        await asyncio.gather(*asyncio.all_tasks(), return_exceptions=True)
    except Exception as e:
        logger.error(f'Ошибка при завершении работы: {e}')

async def shutdown_webhooks(application):
    """Shutdown webhook handlers"""
    logger.info('Остановка вебхуков...')
    await application.stop()
    logger.info('Остановка бота.')

async def main():
    """Main application entry point"""
    # Validate client code
    if validate_client_code is not None:
        try:
            is_valid = await validate_client_code()
            if not is_valid:
                print('❌ Бот не активирован. Проверьте ваш клиентский код.')
                sys.exit(1)
        except Exception as e:
            print(f'⚠️ Ошибка при проверке клиентского кода: {e}')
            print('ℹ Продолжаем без проверки...')
    else:
        print('⚠️ Модуль проверки клиентского кода не найден')
        print('ℹ Продолжаем без проверки...')
    
    # Verify integrity
    if MAIN_SECRET is not None:
        expected_secret = 'SOLO-ACCESS-KEY-B4TN-92QX-L7ME'
        if MAIN_SECRET != expected_secret:
            logger.error('Нарушена целостность файлов! Обновитесь с полной заменой папки!')
            return
    else:
        print('⚠️ Модуль проверки целостности не найден')
        print('ℹ Продолжаем без проверки...')
    
    # Register middleware
    if register_middleware is not None:
        register_middleware(dispatcher, sessionmaker=async_session_maker)
    else:
        print('⚠️ Middleware registration skipped')
    
    # Include routers
    if router is not None:
        try:
            dispatcher.include_router(router)
        except Exception as e:
            logger.warning(f"Failed to include main router: {e}")
    
    if DEV_MODE:
        logger.info('Запуск в режиме разработки...')
        await bot_instance.delete_webhook()
        await init_db()
        
        # Start background tasks
        tasks = [asyncio.create_task(general_notifications(bot_instance, sessionmaker=async_session_maker))]
        
        if PING_TIME > 0:
            async def check_servers_task():
                async with async_session_maker() as session:
                    await check_servers(session)
            tasks.append(asyncio.create_task(check_servers_task()))
        
        if BACKUP_TIME > 0:
            tasks.append(asyncio.create_task(backup_loop()))
        
        # Start API if enabled
        if API_ENABLE:
            logger.info('🔧 DEV: Запускаем API...')
            api_cmd = [
                sys.executable,
                '-m',
                'uvicorn',
                'api.main:app',
                '--host',
                API_HOST,
                '--port',
                str(API_PORT),
                '--reload'
            ]
            if not API_LOGGING:
                api_cmd += ['--log-level', 'critical']
            subprocess.Popen(api_cmd)
        
        # Start polling
        await dispatcher.start_polling(bot_instance)
        
        logger.info('Polling остановлен в режиме разработки. Отмена фоновых задач...')
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    
    else:
        logger.info('Запуск в production режиме...')
        
        # Create aiohttp application
        application = web_module.Application()
        application['sessionmaker'] = async_session_maker
        
        # Add startup and shutdown handlers
        application.on_startup.append(on_startup)
        application.on_shutdown.append(on_shutdown)
        
        # Add payment webhook routes
        if YOOKASSA_ENABLE:
            application.router.add_post('/yookassa/webhook', yookassa_webhook)
        if YOOMONEY_ENABLE:
            application.router.add_post('/yoomoney/webhook', yoomoney_webhook)
        if CRYPTO_BOT_ENABLE:
            application.router.add_post('/cryptobot/webhook', cryptobot_webhook)
        if ROBOKASSA_ENABLE:
            application.router.add_post('/robokassa/webhook', robokassa_webhook)
        if FREEKASSA_ENABLE:
            application.router.add_get('/freekassa/webhook', freekassa_webhook)
        
        # Add subscription route
        application.router.add_get(f'{SUB_PATH}{{email}}/{{tg_id}}', handle_subscription)
        
        # Register web routes
        await register_web_routes(application.router)
        
        # Setup webhook
        setup_application(application, dispatcher, bot=bot_instance)
        
        # Start webhook server
        runner = web_module.AppRunner(application)
        await runner.setup()
        site = web_module.TCPSite(runner, host=WEBAPP_HOST, port=WEBAPP_PORT)
        await site.start()
        
        # Start API server if enabled
        if API_ENABLE:
            asyncio.create_task(start_api_server())
        
        logger.info(f'URL вебхука: {WEBHOOK_URL}')
        
        # Wait for shutdown signal
        shutdown_event = asyncio.Event()
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, shutdown_event.set)
        
        try:
            await shutdown_event.wait()
        finally:
            # Cancel all tasks
            remaining_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            for task in remaining_tasks:
                try:
                    task.cancel()
                except Exception as e:
                    logger.error(e)
            await asyncio.gather(*remaining_tasks, return_exceptions=True)

if __name__ == '__main__':
    install_cli_command()
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f'Ошибка при запуске приложения:\n{e}')
