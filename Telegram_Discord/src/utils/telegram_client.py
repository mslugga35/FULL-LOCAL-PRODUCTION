"""
Telegram client utilities with session management and rate limit handling
"""
import os
import asyncio
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
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


def setup_collector_db(inbox_dir: str) -> sqlite3.Connection:
    """Initialize SQLite database for persistent deduplication"""
    base_path = Path(inbox_dir).parent
    state_dir = base_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    db_path = state_dir / "collector.sqlite3"
    db = sqlite3.connect(str(db_path), check_same_thread=False, isolation_level=None)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA temp_store=MEMORY")
    db.execute("PRAGMA auto_vacuum=INCREMENTAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS collected (
            chat_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (chat_id, message_id)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_collected_at ON collected(collected_at)")
    db.commit()
    return db


def purge_old_collector(db: sqlite3.Connection, logger=None):
    """Remove entries older than 24 hours to prevent unbounded growth"""
    try:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute("DELETE FROM collected WHERE collected_at < datetime('now','-1 day')")
        deleted = cursor.rowcount
        db.execute("COMMIT")
        db.execute("PRAGMA incremental_vacuum(200)")
        if logger and deleted > 0:
            logger.info(f"TTL purge: removed {deleted} entries older than 24h")
    except Exception as e:
        if logger:
            logger.warning(f"TTL purge failed: {e}")


def ttl_loop_collector(db: sqlite3.Connection, logger=None, interval_seconds=3600):
    """Background thread to purge old entries every hour"""
    import time
    while True:
        time.sleep(interval_seconds)
        purge_old_collector(db, logger)


async def backfill_messages(
    client: TelegramClient,
    chat_ids: List[int],
    inbox_dir: str,
    db: sqlite3.Connection,
    media_download: bool = True,
    limit: int = 30,
    max_age_hours: int = 4,
    logger=None
) -> int:
    """
    Backfill last N messages from each chat on startup.
    Skips already-collected messages via the sqlite DB.
    Only backfills messages from the last max_age_hours to prevent resurfacing old picks.
    
    Returns:
        Total number of new messages collected
    """
    total_new = 0
    
    # Time cutoff - only backfill messages newer than this
    from datetime import timedelta, timezone
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    if logger:
        logger.info(f"Backfill cutoff: only messages after {cutoff_time.isoformat()}")
    
    # Cache chat titles to avoid repeated API calls
    chat_titles: Dict[int, str] = {}
    
    for chat_id in chat_ids:
        try:
            if logger:
                logger.info(f"Backfilling chat {chat_id} (last {limit} messages)...")
            
            # Get chat title once per chat (not per message)
            if chat_id not in chat_titles:
                try:
                    entity = await client.get_entity(chat_id)
                    chat_titles[chat_id] = getattr(entity, "title", None)
                except Exception:
                    chat_titles[chat_id] = None
            
            new_count = 0
            skipped_old = 0
            async for message in client.iter_messages(chat_id, limit=limit):
                try:
                    # Skip messages older than cutoff time (prevents resurfacing old picks)
                    if message.date and message.date < cutoff_time:
                        skipped_old += 1
                        continue
                    
                    # Check for duplicate
                    msg_chat_id = str(chat_id)
                    msg_id = int(message.id)
                    
                    try:
                        db.execute("INSERT INTO collected(chat_id, message_id) VALUES (?,?)", (msg_chat_id, msg_id))
                        db.commit()
                    except sqlite3.IntegrityError:
                        # Already collected - skip silently
                        continue
                    
                    # Extract message data
                    media_type = "text"
                    if isinstance(message.media, MessageMediaPhoto):
                        media_type = "photo"
                    elif isinstance(message.media, MessageMediaDocument):
                        media_type = "document"
                    elif message.media:
                        media_type = "other_media"
                    
                    payload = {
                        "id": message.id,
                        "chat_id": chat_id,
                        "chat_title": chat_titles.get(chat_id),
                        "sender_id": message.sender_id,
                        "type": media_type,
                        "text": message.message or "",
                        "media_path": None,
                        "ts_iso": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        "has_media": bool(message.media),
                        "raw": message.to_dict(),
                        "backfilled": True,  # Mark as backfilled
                    }
                    
                    # Download media if present
                    if message.media and media_download:
                        media_dir = Path(inbox_dir) / "media" / datetime.now().strftime("%Y%m%d")
                        media_path = await download_media_safe(client, message.media, str(media_dir), logger)
                        if media_path:
                            payload["media_path"] = media_path
                    
                    # Save to inbox
                    msg_filename = f"{chat_id}_{message.id}_{datetime.now().strftime('%H%M%S')}.json"
                    out_path = Path(inbox_dir) / msg_filename
                    
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
                    
                    new_count += 1
                    
                except Exception as e:
                    if logger:
                        logger.warning(f"Error backfilling message {message.id}: {e}")
                    continue
            
            if logger:
                if new_count > 0 or skipped_old > 0:
                    logger.info(f"  → Chat {chat_id}: {new_count} new, {skipped_old} skipped (older than {max_age_hours}h)")
            
            total_new += new_count
            await asyncio.sleep(1)  # Rate limit between chats
            
        except FloodWaitError as e:
            await handle_flood_wait(e, logger)
        except Exception as e:
            if logger:
                logger.warning(f"Error backfilling chat {chat_id}: {e}")
            continue
    
    return total_new


async def start_collector(
    chat_ids: List[int],
    inbox_dir: str,
    media_download: bool = True,
    backfill_count: int = 30,
    logger=None
) -> None:
    """
    Start Telegram message collector with duplicate detection and backfill

    Args:
        chat_ids: List of Telegram chat IDs to monitor
        inbox_dir: Directory to save messages
        media_download: Whether to download media
        backfill_count: Number of messages to backfill per chat on startup (0 to disable)
        logger: Optional logger instance
    """
    Path(inbox_dir).mkdir(parents=True, exist_ok=True)

    # Initialize SQLite database for deduplication
    db = setup_collector_db(inbox_dir)
    if logger:
        logger.info("Collector DB initialized with TTL cleanup")

    # One-shot cleanup of old entries
    purge_old_collector(db, logger)

    # Start background TTL cleanup thread
    threading.Thread(target=ttl_loop_collector, args=(db, logger), daemon=True).start()
    if logger:
        logger.info("TTL cleanup thread started (purges entries >24h every hour)")

    client = build_client()

    # Connect with retry logic
    max_connect_retries = 5
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
    
    # Backfill recent messages on startup
    if backfill_count > 0:
        if logger:
            logger.info(f"Starting backfill (last {backfill_count} messages per chat)...")
        try:
            total = await backfill_messages(client, chat_ids, inbox_dir, db, media_download, backfill_count, max_age_hours=4, logger=logger)
            if logger:
                logger.info(f"Backfill complete: {total} new messages collected")
        except Exception as e:
            if logger:
                logger.warning(f"Backfill failed (continuing anyway): {e}")

    @client.on(events.NewMessage(chats=chat_ids))
    async def handler(event):
        try:
            # Check for duplicate in SQLite
            chat_id = str(event.chat_id)
            message_id = int(event.message.id)

            try:
                db.execute("INSERT INTO collected(chat_id, message_id) VALUES (?,?)", (chat_id, message_id))
                db.commit()
            except sqlite3.IntegrityError:
                # Already collected - skip
                if logger:
                    logger.info(f"⚠️ Skipping duplicate message: {chat_id}_{message_id}")
                return

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

    # Health check task with auto-reconnect
    async def health_check():
        reconnect_attempts = 0
        max_reconnect = 5
        
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            if logger:
                logger.info("[HEALTH] Telegram collector alive")
                logger.info(f"Connected: {client.is_connected()}")
            
            # Auto-reconnect if disconnected
            if not client.is_connected():
                reconnect_attempts += 1
                if logger:
                    logger.warning(f"Connection lost! Reconnect attempt {reconnect_attempts}/{max_reconnect}")
                
                if reconnect_attempts > max_reconnect:
                    if logger:
                        logger.error("Max reconnect attempts reached. Restarting collector...")
                    # Exit to let PM2 restart us
                    os._exit(1)
                
                try:
                    await client.connect()
                    if client.is_connected():
                        reconnect_attempts = 0
                        if logger:
                            logger.info("Reconnected successfully!")
                except Exception as e:
                    if logger:
                        logger.error(f"Reconnect failed: {e}")
                    await asyncio.sleep(30 * reconnect_attempts)  # Backoff

    # Start health check
    asyncio.create_task(health_check())

    # Run with session error recovery
    session_errors = 0
    max_session_errors = 10
    
    while True:
        try:
            await client.run_until_disconnected()
            break  # Clean exit
        except KeyboardInterrupt:
            if logger:
                logger.info("Telegram collector shutting down...")
            break
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for session-related errors
            if "session" in error_msg or "security" in error_msg or "auth" in error_msg:
                session_errors += 1
                if logger:
                    logger.warning(f"Session error ({session_errors}/{max_session_errors}): {e}")
                
                if session_errors >= max_session_errors:
                    if logger:
                        logger.error("Too many session errors. Exiting for PM2 restart...")
                    break
                
                # Try to reconnect
                await asyncio.sleep(5)
                try:
                    await client.disconnect()
                    await asyncio.sleep(2)
                    await client.connect()
                    if logger:
                        logger.info("Reconnected after session error")
                except Exception as re:
                    if logger:
                        logger.error(f"Reconnect after session error failed: {re}")
            else:
                if logger:
                    logger.error(f"Unexpected error: {e}")
                break
    
    await client.disconnect()