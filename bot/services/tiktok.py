import asyncio
import logging
import os
import time
from pathlib import Path
from yt_dlp import YoutubeDL
from ..config import DOWNLOAD_DIR, MAX_FILE_SIZE, PROXY_URL, DOWNLOAD_TIMEOUT

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL = 3600  # 1 час
MAX_FILE_AGE = 86400  # 24 часа


async def download_video(url: str, retry: int = 2) -> str | None:
    for attempt in range(retry + 1):
        try:
            output_template = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": DOWNLOAD_TIMEOUT,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            }

            if PROXY_URL:
                ydl_opts["proxy"] = PROXY_URL

            loop = asyncio.get_event_loop()
            info = await asyncio.wait_for(
                loop.run_in_executor(None, _download_with_ydl, url, ydl_opts),
                timeout=DOWNLOAD_TIMEOUT + 10
            )

            if not info:
                if attempt < retry:
                    logger.warning(f"Retry {attempt + 1}/{retry}")
                    continue
                return None

            video_id = info.get("id")
            ext = info.get("ext", "mp4")
            video_path = DOWNLOAD_DIR / f"{video_id}.{ext}"

            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return None

            file_size = video_path.stat().st_size

            if file_size > MAX_FILE_SIZE:
                cleanup_file(str(video_path))
                logger.warning(f"File too large: {file_size / 1024 / 1024:.1f}MB")
                return None

            return str(video_path)

        except asyncio.TimeoutError:
            logger.warning(f"Download timeout (attempt {attempt + 1}/{retry + 1})")
            if attempt < retry:
                continue
            return None
        except Exception as e:
            logger.warning(f"Error attempt {attempt + 1}/{retry + 1}: {type(e).__name__}: {e}")
            if attempt < retry:
                continue
            return None

    return None


def _download_with_ydl(url: str, opts: dict) -> dict | None:
    try:
        logger.info(f"Downloading: {url}")
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            logger.info(f"Downloaded successfully: {info.get('id')}")
            return info
    except Exception as e:
        logger.error(f"YoutubeDL error: {type(e).__name__}: {e}")
        return None


def cleanup_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file: {e}")


def cleanup_old_files():
    try:
        current_time = time.time()
        for file_path in DOWNLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > MAX_FILE_AGE:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old file: {file_path}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
