import logging
from pathlib import Path
from aiogram.types import Message
from config import MAX_FILE_SIZE

logger = logging.getLogger(__name__)


async def send_video_safe(message: Message, video_path: str) -> bool:
    try:
        file_size = Path(video_path).stat().st_size

        if file_size > MAX_FILE_SIZE:
            await message.answer(
                f"❌ Видео слишком большое ({file_size / 1024 / 1024:.1f} MB). "
                f"Максимум: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
            )
            return False

        with open(video_path, "rb") as video_file:
            await message.answer_video(video_file)
        return True

    except Exception as e:
        logger.error(f"Error sending video: {e}")
        await message.answer("❌ Ошибка при отправке видео")
        return False


async def send_error(message: Message, error_type: str = "unknown"):
    error_messages = {
        "invalid_url": "❌ Некорректная ссылка на TikTok",
        "download_failed": "❌ Не удалось скачать видео",
        "file_too_large": "❌ Видео слишком большое",
        "timeout": "❌ Загрузка заняла слишком много времени",
        "unknown": "❌ Неизвестная ошибка. Попробуй позже",
    }

    message_text = error_messages.get(error_type, error_messages["unknown"])
    await message.answer(message_text)


async def send_status(message: Message, status: str):
    status_messages = {
        "downloading": "⏳ Загружаю видео...",
        "processing": "⚙️ Обрабатываю видео...",
        "sending": "📤 Отправляю видео...",
    }

    message_text = status_messages.get(status, status)
    await message.answer(message_text)
