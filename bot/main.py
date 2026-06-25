import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import BOT_TOKEN, LOG_LEVEL, DOWNLOAD_DIR
from handlers import video

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

file_handler = RotatingFileHandler(
    log_dir / "bot.log",
    maxBytes=10_000_000,
    backupCount=5
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=LOG_LEVEL,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Справка по использованию"),
    ]
    await bot.set_my_commands(commands)


async def cleanup_task():
    while True:
        try:
            from services.tiktok import cleanup_old_files
            cleanup_old_files()
            await asyncio.sleep(3600)  # Каждый час
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
            await asyncio.sleep(300)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(video.router)

    await set_commands(bot)

    asyncio.create_task(cleanup_task())

    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
