import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from services import tiktok

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Привет! Я бот для скачивания видео с TikTok\n\n"
        "Просто отправь мне ссылку на видео TikTok, и я его скачаю и отправлю тебе"
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "📖 Справка:\n\n"
        "1. Отправь ссылку на видео TikTok\n"
        "2. Подожди загрузки видео\n"
        "3. Получи видео в чате\n\n"
        "⚠️ Максимальный размер видео: 50 MB"
    )


@router.message(F.text)
async def video_handler(message: Message):
    if not is_tiktok_url(message.text):
        await message.answer("❌ Пожалуйста, отправь корректную ссылку на видео TikTok")
        return

    status_msg = await message.answer("⏳ Загружаю видео...")

    try:
        video_path = await tiktok.download_video(message.text)

        if not video_path:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="❌ Не удалось скачать видео. Возможно видео удалено или недоступно"
            )
            return

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text="📤 Отправляю видео..."
        )

        video_file = FSInputFile(video_path)
        await message.answer_video(video_file)

        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

        tiktok.cleanup_file(video_path)

    except Exception as e:
        logger.error(f"Error handling video: {type(e).__name__}: {e}")
        await message.answer("❌ Ошибка при обработке видео. Попробуй позже")


def is_tiktok_url(text: str) -> bool:
    return "tiktok.com" in text.lower() or "vm.tiktok.com" in text.lower() or "vt.tiktok.com" in text.lower()
