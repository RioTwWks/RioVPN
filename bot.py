import asyncio
import logging
from aiogram import Bot, Dispatcher

# from config_reader import config

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from decouple import config

from handlers import start_questions, submit_application
# from aiogram.fsm.storage.memory import MemoryStorage


async def main():
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Объект бота
    # bot = Bot(token=config.bot_token.get_secret_value())
    bot = Bot(token=config('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Диспетчер
    dp = Dispatcher()

    dp.include_routers(start_questions.router, submit_application.router)

    # Запускаем бота и пропускаем все накопленные входящие
    # Этот метод можно вызвать даже если у вас поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
