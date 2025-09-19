#!/usr/bin/env python3
"""
FIXED Telegram Collector with proper timeout handling and session management
Addresses:
- Connection timeout issues
- Session lock management
- Multiple instance prevention
- Proper error handling and reconnection
"""
import os
import sys
import asyncio
import json
import time
import pathlib
import logging
import signal
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import RPCError, NetworkError
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
SESSION_STRING = os.getenv("TELEGRAM_STRING_SESSION", "1AQAOMTQ5LjE1NC4xNzUuNTcBu2g+yaG4eWVh5epPtcgWfQTPkqasIdvsxCj68U7clUx9mn3LsVTRIXr/0xJoWABsu/2Khznce7EyhPh0wMw4aFTKllNmUA+iJsGib4sQfpd5dMcg0Ua3BR9JCx596L7qNzAhSda7R2grZFv5cnyx5oT39iXIA3edgHUpf0n+0XwfFFwK8oIqoJgPvoThCpwPit2iCXGM1LERLzssLErvGYzUeAklhKBvle3OJJRFPz4GQIkSRiVQLutLHHXUh3uLws7Pauq/fuhTbd8KxQ5987wcrXlwGI7iUOskQkc+vGlDuXUr3pgbsRHZ5qnIycCnWE3GhO/ns5OtXvJ8PbvkMjQ=")
INBOX = r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\inbox"
LOCKFILE = r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\telegram_collector.lock"
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

# Message Queue Directory Configuration
MESSAGE_QUEUE_BASE = r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\message_queue"

# Chat ID to Directory Mapping
QUEUE_DIRS = {
    -1002177758646: "paid_uatb",                                    # UATB → paid_uatb
    -1002470080886: "paid_diamond",                                 # Diamond/Chamba → paid_diamond
    -1002592669126: "free_cappers\\cappers_free",                   # Cappers Free → free_cappers\cappers_free
    -1001560546587: "free_cappers\\cappers_leaked",                # Cappers Leaked → free_cappers\cappers_leaked
    -1002608783933: "free_cappers\\exclusive_cappers",             # Exclusive Cappers → free_cappers\exclusive_cappers
}

# Connection settings
CONNECTION_TIMEOUT = 30  # seconds
AUTH_TIMEOUT = 15       # seconds
RECONNECT_DELAY = 10    # seconds
MAX_RECONNECTS = 5

# Channels to monitor
CHANNELS = [
    -1002592669126,  # Cappers Free
    -1001560546587,  # Cappers Leaked
    -1002608783933,  # Exclusive Cappers
    -1002177758646,  # UATB
    -1002470080886,  # Diamond/Chamba
]

# Global variables
client = None
running = True
reconnect_count = 0

def acquire_lock():
    """Acquire a file lock to ensure single instance"""
    try:
        if os.path.exists(LOCKFILE):
            try:
                with open(LOCKFILE, 'r') as f:
                    old_pid = int(f.read().strip())
                # Check if process exists
                import subprocess
                result = subprocess.run(['tasklist', '/fi', f'PID eq {old_pid}'],
                                      capture_output=True, text=True)
                if str(old_pid) in result.stdout:
                    logger.error(f"Another instance is running (PID={old_pid})")
                    return False
                else:
                    logger.warning(f"Removing stale lock file (PID={old_pid} not running)")
                    os.remove(LOCKFILE)
            except Exception as e:
                logger.warning(f"Error checking lock file: {e}")
                try:
                    os.remove(LOCKFILE)
                except:
                    pass

        with open(LOCKFILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"Lock acquired (PID={os.getpid()})")
        return True
    except Exception as e:
        logger.error(f"Failed to acquire lock: {e}")
        return False

def release_lock():
    """Release the file lock"""
    try:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
            logger.info("Lock released")
    except Exception as e:
        logger.warning(f"Error releasing lock: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False

def save_message(channel_name, text, message_id, chat_id, has_media=False, media_path=None):
    """Save message to appropriate queue directory based on chat_id"""
    try:
        # Determine queue directory from chat_id
        queue_subdir = QUEUE_DIRS.get(chat_id, "unknown")
        queue_path = os.path.join(MESSAGE_QUEUE_BASE, queue_subdir)

        # Ensure queue directory exists
        pathlib.Path(queue_path).mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        safe_name = channel_name.replace(" ", "_").replace("/", "_")
        filename = f"{ts}_{safe_name}_{message_id}.json"
        filepath = os.path.join(queue_path, filename)

        payload = {
            "source": "telegram",
            "channel": channel_name,
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "has_media": has_media,
            "media_file": os.path.basename(media_path) if media_path else None,
            "timestamp": datetime.now().isoformat(),
            "created_utc": int(time.time()),
            "queue_path": queue_subdir
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved message to {queue_subdir}: {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        return False

@events.register(events.NewMessage(chats=CHANNELS))
async def handle_message(event):
    """Handle new messages with proper error handling and routing"""
    try:
        chat = await event.get_chat()
        chat_title = getattr(chat, "title", f"Chat_{chat.id}")
        chat_id = chat.id

        text = event.message.message or ""
        message_id = event.message.id

        preview = text[:80].replace('\n', ' ')
        queue_dir = QUEUE_DIRS.get(chat_id, "unknown")
        logger.info(f"New message from {chat_title} (ID: {chat_id}) → {queue_dir}: {preview}...")

        media_path = None
        if event.message.photo or event.message.document:
            try:
                # Create media directory in appropriate queue folder
                queue_subdir = QUEUE_DIRS.get(chat_id, "unknown")
                queue_media_path = os.path.join(MESSAGE_QUEUE_BASE, queue_subdir, "media")
                os.makedirs(queue_media_path, exist_ok=True)

                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                media_file = f"{ts}_{message_id}"
                media_path = os.path.join(queue_media_path, media_file)

                downloaded = await event.message.download_media(file=media_path)
                if downloaded:
                    logger.info(f"Downloaded media to {queue_subdir}: {os.path.basename(downloaded)}")
                    media_path = downloaded
            except Exception as e:
                logger.error(f"Media download failed: {e}")
                media_path = None

        save_message(
            chat_title,
            text,
            message_id,
            chat_id,
            has_media=bool(media_path),
            media_path=media_path
        )

    except Exception as e:
        logger.error(f"Message handler error: {e}")

async def connect_with_timeout():
    """Connect to Telegram with timeout and proper error handling"""
    global client, reconnect_count

    try:
        logger.info("Creating Telegram client...")
        client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

        # Add event handler
        client.add_event_handler(handle_message)

        logger.info(f"Connecting (timeout: {CONNECTION_TIMEOUT}s)...")
        await asyncio.wait_for(client.connect(), timeout=CONNECTION_TIMEOUT)

        logger.info(f"Checking authorization (timeout: {AUTH_TIMEOUT}s)...")
        is_authorized = await asyncio.wait_for(client.is_user_authorized(), timeout=AUTH_TIMEOUT)

        if not is_authorized:
            logger.error("Session not authorized! Run auth script first.")
            return False

        # Get user info
        me = await client.get_me()
        logger.info(f"Connected as: {me.first_name} (@{me.username})")

        # Verify channel access
        logger.info("Verifying channel access...")
        accessible_channels = 0
        for ch_id in CHANNELS:
            try:
                entity = await client.get_entity(ch_id)
                logger.info(f"  ✓ {entity.title}")
                accessible_channels += 1
            except Exception as e:
                logger.warning(f"  ✗ Channel {ch_id}: {e}")

        logger.info(f"Ready! Monitoring {accessible_channels}/{len(CHANNELS)} channels")
        reconnect_count = 0  # Reset reconnect counter on success
        return True

    except asyncio.TimeoutError:
        logger.error("Connection timeout - check network/firewall")
        return False
    except RPCError as e:
        logger.error(f"Telegram API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False

async def main_loop():
    """Main loop with reconnection handling"""
    global running, reconnect_count

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=== FIXED TELEGRAM COLLECTOR ===")
    logger.info(f"Inbox: {INBOX}")
    logger.info(f"Lockfile: {LOCKFILE}")
    logger.info("=" * 50)

    # Ensure directories exist
    pathlib.Path(INBOX).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(INBOX, "media")).mkdir(parents=True, exist_ok=True)
    pathlib.Path("logs").mkdir(parents=True, exist_ok=True)

    # Ensure message queue directories exist
    for chat_id, queue_dir in QUEUE_DIRS.items():
        queue_path = os.path.join(MESSAGE_QUEUE_BASE, queue_dir)
        pathlib.Path(queue_path).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(queue_path, "media")).mkdir(parents=True, exist_ok=True)
        logger.info(f"Queue directory ready: {queue_path}")

    while running and reconnect_count < MAX_RECONNECTS:
        try:
            if await connect_with_timeout():
                logger.info("Starting message loop...")
                await client.run_until_disconnected()
            else:
                reconnect_count += 1
                if reconnect_count < MAX_RECONNECTS:
                    logger.warning(f"Reconnection attempt {reconnect_count}/{MAX_RECONNECTS} in {RECONNECT_DELAY}s...")
                    await asyncio.sleep(RECONNECT_DELAY)
                else:
                    logger.error("Max reconnection attempts reached")
                    break

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            running = False
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            reconnect_count += 1
            if reconnect_count < MAX_RECONNECTS:
                await asyncio.sleep(RECONNECT_DELAY)

    # Cleanup
    if client:
        try:
            await client.disconnect()
            logger.info("Client disconnected")
        except:
            pass

async def main():
    """Main function"""
    if not acquire_lock():
        logger.error("Could not acquire lock - another instance may be running")
        sys.exit(1)

    try:
        await main_loop()
    finally:
        release_lock()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        release_lock()
        sys.exit(1)