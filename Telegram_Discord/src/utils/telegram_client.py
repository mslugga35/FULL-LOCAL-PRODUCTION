"""
Telegram client utilities with session management and rate limit handling
"""
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument


def getenv(name: str) -> str:
    """Get environment variable, strip whitespace"""
    return os.getenv(name, "").strip()


def build_client() -> TelegramClient:
    """
    Build Telegram client with session management

    Returns:
        Configured TelegramClient instance
    """
    api_id = getenv("TELEGRAM_API_ID")
    api_hash = getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        raise RuntimeError("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH")

    # Try string session first, then file session
    sess_str = getenv("TELEGRAM_SESSION")
    sess_file = getenv("TELEGRAM_SESSION_FILE")

    if sess_str:
        client = TelegramClient(StringSession(sess_str), int(api_id), api_hash)
    else:
        sess_path = sess_file or "tg.session"
        client = TelegramClient(sess_path, int(api_id), api_hash)

    return client


async def handle_flood_wait(exc: FloodWaitError, logger=None) -> None:
    """Handle Telegram flood wait with exponential backoff"""
    wait_time = exc.seconds
    if logger:
        logger.warning(f"FloodWaitError: Waiting {wait_time} seconds")
    await asyncio.sleep(wait_time + 5)  # Add 5s buffer


async def download_media_safe(client: TelegramClient, media, media_dir: str, logger=None) -> Optional[str]:
    """
    Download media with retry logic

    Args:
        client: Telegram client
        media: Media object
        media_dir: Directory to save media
        logger: Optional logger

    Returns:
        Path to downloaded file or None
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            Path(media_dir).mkdir(parents=True, exist_ok=True)
            file_path = await client.download_media(media, file=media_dir)
            return file_path
        except FloodWaitError as e:
            await handle_flood_wait(e, logger)
        except Exception as e:
            if logger:
                logger.warning(f"Media download attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return None


def extract_message_data(event) -> Dict[str, Any]:
    """
    Extract structured data from Telegram message event

    Args:
        event: Telegram message event

    Returns:
        Dictionary with message data
    """
    msg = event.message

    # Determine media type
    media_type = "text"
    if isinstance(msg.media, MessageMediaPhoto):
        media_type = "photo"
    elif isinstance(msg.media, MessageMediaDocument):
        media_type = "document"
    elif msg.media:
        media_type = "other_media"

    payload = {
        "id": msg.id,
        "chat_id": event.chat_id,
        "chat_title": getattr(event.chat, "title", None),
        "sender_id": msg.sender_id,
        "type": media_type,
        "text": msg.message or "",
        "media_path": None,
        "ts_iso": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "has_media": bool(msg.media),
        "raw": msg.to_dict(),
    }

    return payload


async def start_collector(
    chat_ids: List[int],
    inbox_dir: str,
    media_download: bool = True,
    logger=None
) -> None:
    """
    Start Telegram message collector

    Args:
        chat_ids: List of Telegram chat IDs to monitor
        inbox_dir: Directory to save messages
        media_download: Whether to download media
        logger: Optional logger instance
    """
    Path(inbox_dir).mkdir(parents=True, exist_ok=True)

    client = build_client()

    # Connect with retry logic
    max_connect_retries = 3
    for attempt in range(max_connect_retries):
        try:
            await client.start()
            break
        except FloodWaitError as e:
            await handle_flood_wait(e, logger)
        except Exception as e:
            if logger:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt == max_connect_retries - 1:
                raise
            await asyncio.sleep(5 * (attempt + 1))

    if logger:
        logger.info(f"Telegram collector started. Monitoring {len(chat_ids)} chats")
        logger.info(f"Chat IDs: {chat_ids}")

    @client.on(events.NewMessage(chats=chat_ids))
    async def handler(event):
        try:
            payload = extract_message_data(event)

            # Download media if present
            if event.message.media and media_download:
                media_dir = Path(inbox_dir) / "media" / datetime.now().strftime("%Y%m%d")
                media_path = await download_media_safe(
                    client,
                    event.message.media,
                    str(media_dir),
                    logger
                )
                if media_path:
                    payload["media_path"] = media_path

            # Save message to inbox
            msg_filename = f"{event.chat_id}_{event.message.id}_{datetime.now().strftime('%H%M%S')}.json"
            out_path = Path(inbox_dir) / msg_filename

            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

            if logger:
                logger.info(f"Saved message to inbox: {out_path}")
                logger.debug(f"Message type: {payload['type']}, Has media: {payload['has_media']}")

        except Exception as e:
            if logger:
                logger.error(f"Error processing message: {e}", exc_info=True)

    # Health check task
    async def health_check():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            if logger:
                logger.info("[HEALTH] Telegram collector alive")
                logger.info(f"Connected: {client.is_connected()}")

    # Start health check
    asyncio.create_task(health_check())

    # Run until disconnected
    try:
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        if logger:
            logger.info("Telegram collector shutting down...")
    finally:
        await client.disconnect()