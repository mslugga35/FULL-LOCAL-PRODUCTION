#!/usr/bin/env python3
"""
Updated Telegram Collector with routing_config.json integration
Features:
- Uses routing_config.json for channel configuration
- Enhanced Windows path handling
- Improved error handling and reconnection
- Production-ready logging and monitoring
- System controller integration
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

# Setup logging with Windows-compatible paths
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_collector_updated.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class TelegramCollector:
    def __init__(self, config_file="routing_config.json"):
        """Initialize the Telegram collector with routing configuration"""
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_paths()
        self.setup_telegram_config()

        # Connection settings
        self.CONNECTION_TIMEOUT = 30
        self.AUTH_TIMEOUT = 15
        self.RECONNECT_DELAY = 10
        self.MAX_RECONNECTS = 5

        # Global variables
        self.client = None
        self.running = True
        self.reconnect_count = 0

        # Lock file for single instance
        self.LOCKFILE = os.path.join(os.path.dirname(__file__), "telegram_collector_updated.lock")

    def load_config(self):
        """Load routing configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")
            raise

    def setup_paths(self):
        """Setup Windows-compatible paths from configuration"""
        self.MESSAGE_QUEUE_BASE = self.config["windows_base_path"]

        # Extract enabled channels and their queue paths
        self.CHANNELS = []
        self.QUEUE_DIRS = {}
        self.CHANNEL_INFO = {}

        for chat_id_str, channel_config in self.config["telegram_channels"].items():
            if channel_config.get("enabled", True):
                chat_id = int(chat_id_str)
                self.CHANNELS.append(chat_id)

                # Use Windows path separators from config
                queue_path = channel_config["queue_path"]
                self.QUEUE_DIRS[chat_id] = queue_path

                # Store additional channel info for Discord forwarder
                self.CHANNEL_INFO[chat_id] = {
                    "name": channel_config["name"],
                    "display_name": channel_config["display_name"],
                    "type": channel_config["type"],
                    "queue_path": queue_path
                }

        logger.info(f"Configured to monitor {len(self.CHANNELS)} channels")
        for chat_id in self.CHANNELS:
            logger.info(f"  {chat_id} → {self.QUEUE_DIRS[chat_id]}")

    def setup_telegram_config(self):
        """Setup Telegram API configuration"""
        self.SESSION_STRING = os.getenv("TELEGRAM_STRING_SESSION",
            "1AQAOMTQ5LjE1NC4xNzUuNTcBu2g+yaG4eWVh5epPtcgWfQTPkqasIdvsxCj68U7clUx9mn3LsVTRIXr/0xJoWABsu/2Khznce7EyhPh0wMw4aFTKllNmUA+iJsGib4sQfpd5dMcg0Ua3BR9JCx596L7qNzAhSda7R2grZFv5cnyx5oT39iXIA3edgHUpf0n+0XwfFFwK8oIqoJgPvoThCpwPit2iCXGM1LERLzssLErvGYzUeAklhKBvle3OJJRFPz4GQIkSRiVQLutLHHXUh3uLws7Pauq/fuhTbd8KxQ5987wcrXlwGI7iUOskQkc+vGlDuXUr3pgbsRHZ5qnIycCnWE3GhO/ns5OtXvJ8PbvkMjQ=")
        self.api_id = 29479443
        self.api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

    def acquire_lock(self):
        """Acquire a file lock to ensure single instance"""
        try:
            if os.path.exists(self.LOCKFILE):
                try:
                    with open(self.LOCKFILE, 'r') as f:
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
                        os.remove(self.LOCKFILE)
                except Exception as e:
                    logger.warning(f"Error checking lock file: {e}")
                    try:
                        os.remove(self.LOCKFILE)
                    except:
                        pass

            with open(self.LOCKFILE, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"Lock acquired (PID={os.getpid()})")
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    def release_lock(self):
        """Release the file lock"""
        try:
            if os.path.exists(self.LOCKFILE):
                os.remove(self.LOCKFILE)
                logger.info("Lock released")
        except Exception as e:
            logger.warning(f"Error releasing lock: {e}")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def save_message(self, channel_name, text, message_id, chat_id, has_media=False, media_path=None):
        """Save message to appropriate queue directory based on chat_id with Discord forwarder integration"""
        try:
            # Determine queue directory from chat_id
            queue_subdir = self.QUEUE_DIRS.get(chat_id, "unknown")
            queue_path = os.path.join(self.MESSAGE_QUEUE_BASE, queue_subdir)

            # Ensure queue directory exists
            pathlib.Path(queue_path).mkdir(parents=True, exist_ok=True)

            # Create timestamp-based filename
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
            safe_name = channel_name.replace(" ", "_").replace("/", "_").replace("💎", "DIAMOND").replace("🌐", "").replace("💥", "").replace("🔥", "")
            filename = f"{ts}_{safe_name}_{message_id}.json"
            filepath = os.path.join(queue_path, filename)

            # Get channel info for Discord forwarder
            channel_info = self.CHANNEL_INFO.get(chat_id, {})

            # Create enhanced payload for Discord forwarder integration
            payload = {
                # Original fields
                "source": "telegram",
                "channel": channel_name,
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "has_media": has_media,
                "media_file": os.path.basename(media_path) if media_path else None,
                "timestamp": datetime.now().isoformat(),
                "created_utc": int(time.time()),
                "queue_path": queue_subdir,

                # Enhanced fields for Discord forwarder routing
                "routing": {
                    "chat_id": chat_id,
                    "channel_type": channel_info.get("type", "unknown"),
                    "channel_name": channel_info.get("name", channel_name),
                    "display_name": channel_info.get("display_name", channel_name),
                    "queue_directory": queue_subdir,
                    "processor": "paid" if channel_info.get("type") == "paid" else "free"
                },

                # Metadata for processing pipeline
                "processing": {
                    "status": "new",
                    "collector_version": "2.0_routing_config",
                    "windows_path": True,
                    "media_path": media_path if media_path else None
                }
            }

            # Write JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved message to {queue_subdir}: {filename}")
            logger.debug(f"Chat ID {chat_id} → {channel_info.get('name', 'Unknown')} ({channel_info.get('type', 'unknown')})")
            return True

        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return False

    async def handle_message(self, event):
        """Handle new messages with proper error handling and routing"""
        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, "title", f"Chat_{chat.id}")
            chat_id = chat.id

            # Skip if not in our monitored channels
            if chat_id not in self.CHANNELS:
                logger.debug(f"Ignoring message from unmonitored chat: {chat_id}")
                return

            text = event.message.message or ""
            message_id = event.message.id

            preview = text[:80].replace('\n', ' ')
            queue_dir = self.QUEUE_DIRS.get(chat_id, "unknown")
            channel_info = self.CHANNEL_INFO.get(chat_id, {})

            logger.info(f"New message from {channel_info.get('name', chat_title)} (ID: {chat_id}) → {queue_dir}: {preview}...")

            media_path = None
            if event.message.photo or event.message.document:
                try:
                    # Create media directory in appropriate queue folder
                    queue_subdir = self.QUEUE_DIRS.get(chat_id, "unknown")
                    queue_media_path = os.path.join(self.MESSAGE_QUEUE_BASE, queue_subdir, "media")
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

            # Save message with enhanced routing information
            self.save_message(
                chat_title,
                text,
                message_id,
                chat_id,
                has_media=bool(media_path),
                media_path=media_path
            )

        except Exception as e:
            logger.error(f"Message handler error: {e}")

    async def connect_with_timeout(self):
        """Connect to Telegram with timeout and proper error handling"""
        try:
            logger.info("Creating Telegram client...")
            self.client = TelegramClient(StringSession(self.SESSION_STRING), self.api_id, self.api_hash)

            # Add event handler for only our monitored channels
            self.client.add_event_handler(
                self.handle_message,
                events.NewMessage(chats=self.CHANNELS)
            )

            logger.info(f"Connecting (timeout: {self.CONNECTION_TIMEOUT}s)...")
            await asyncio.wait_for(self.client.connect(), timeout=self.CONNECTION_TIMEOUT)

            logger.info(f"Checking authorization (timeout: {self.AUTH_TIMEOUT}s)...")
            is_authorized = await asyncio.wait_for(self.client.is_user_authorized(), timeout=self.AUTH_TIMEOUT)

            if not is_authorized:
                logger.error("Session not authorized! Run auth script first.")
                return False

            # Get user info
            me = await self.client.get_me()
            logger.info(f"Connected as: {me.first_name} (@{me.username})")

            # Verify channel access
            logger.info("Verifying channel access...")
            accessible_channels = 0
            for ch_id in self.CHANNELS:
                try:
                    entity = await self.client.get_entity(ch_id)
                    channel_info = self.CHANNEL_INFO.get(ch_id, {})
                    logger.info(f"  ✓ {entity.title} → {channel_info.get('queue_path', 'unknown')}")
                    accessible_channels += 1
                except Exception as e:
                    logger.warning(f"  ✗ Channel {ch_id}: {e}")

            logger.info(f"Ready! Monitoring {accessible_channels}/{len(self.CHANNELS)} channels")
            self.reconnect_count = 0  # Reset reconnect counter on success
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

    def create_queue_directories(self):
        """Create all necessary queue directories"""
        logger.info("Creating queue directories...")

        for chat_id, queue_dir in self.QUEUE_DIRS.items():
            try:
                queue_path = os.path.join(self.MESSAGE_QUEUE_BASE, queue_dir)
                pathlib.Path(queue_path).mkdir(parents=True, exist_ok=True)
                pathlib.Path(os.path.join(queue_path, "media")).mkdir(parents=True, exist_ok=True)

                channel_info = self.CHANNEL_INFO.get(chat_id, {})
                logger.info(f"Queue directory ready: {queue_path} ({channel_info.get('name', 'Unknown')})")
            except Exception as e:
                logger.error(f"Failed to create queue directory for {chat_id}: {e}")

    async def main_loop(self):
        """Main loop with reconnection handling"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logger.info("=" * 60)
        logger.info("UPDATED TELEGRAM COLLECTOR WITH ROUTING CONFIG")
        logger.info(f"Configuration: {self.config_file}")
        logger.info(f"Message Queue Base: {self.MESSAGE_QUEUE_BASE}")
        logger.info(f"Monitoring {len(self.CHANNELS)} channels")
        logger.info("=" * 60)

        # Ensure directories exist
        pathlib.Path("logs").mkdir(parents=True, exist_ok=True)
        self.create_queue_directories()

        while self.running and self.reconnect_count < self.MAX_RECONNECTS:
            try:
                if await self.connect_with_timeout():
                    logger.info("Starting message loop...")
                    await self.client.run_until_disconnected()
                else:
                    self.reconnect_count += 1
                    if self.reconnect_count < self.MAX_RECONNECTS:
                        logger.warning(f"Reconnection attempt {self.reconnect_count}/{self.MAX_RECONNECTS} in {self.RECONNECT_DELAY}s...")
                        await asyncio.sleep(self.RECONNECT_DELAY)
                    else:
                        logger.error("Max reconnection attempts reached")
                        break

            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                self.reconnect_count += 1
                if self.reconnect_count < self.MAX_RECONNECTS:
                    await asyncio.sleep(self.RECONNECT_DELAY)

        # Cleanup
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("Client disconnected")
            except:
                pass

    async def run(self):
        """Main run function"""
        if not self.acquire_lock():
            logger.error("Could not acquire lock - another instance may be running")
            sys.exit(1)

        try:
            await self.main_loop()
        finally:
            self.release_lock()
            logger.info("Shutdown complete")

async def main():
    """Main function"""
    try:
        collector = TelegramCollector()
        await collector.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)