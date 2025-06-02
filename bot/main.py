import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Импортируем роутеры
from bot.handlers import cars  # основной роутер FSM для сбора марки/мотора

# 1. Подгружаем .env до любого обращения к переменным окружения
load_dotenv()

# 2. Читаем токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не установлена")


async def main() -> None:
    """Точка входа Telegram‑бота."""

    # Базовая конфигурация логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Инициализируем Bot с parse_mode по умолчанию (aiogram >= 3.7)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Памятное FSM‑хранилище (в памяти процесса)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем все роутеры приложения
    dp.include_router(cars.router)

    logging.info("🚀 Bot started and polling updates…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot stopped")
