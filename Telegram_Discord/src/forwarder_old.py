#!/usr/bin/env python
"""
Discord forwarder - sends messages from queues to Discord channels
"""
import os
import sys
import time
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger, log_exception, log_health_check, log_rate_limit
from src.utils.fs import read_json, list_json_files, archive_message
from src.utils.discord_client import DiscordSender, RateLimitException
from src.utils.ocr import extract_text_from_image
from src.utils.picks_formatter import format_clean_picks


# Load environment variables
BASE_PATH = Path("C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord")
load_dotenv(BASE_PATH / ".env")

# Load settings
settings_path = BASE_PATH / "config" / "settings.yaml"
if settings_path.exists():
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = yaml.safe_load(f)
else:
    settings = {
        "paths": {
            "queue": str(BASE_PATH / "message_queue"),
            "archive": str(BASE_PATH / "sent_archive"),
            "logs": str(BASE_PATH / "logs")
        },
        "forwarder": {
            "batch_size": 1,
            "max_retries": 5,
            "retry_backoff_seconds": 2
        },
        "ocr": {
            "enabled": False
        }
    }

# Load discord targets
targets_path = BASE_PATH / "config" / "discord_targets.yaml"
if targets_path.exists():
    with open(targets_path, 'r', encoding='utf-8') as f:
        discord_targets = yaml.safe_load(f)
else:
    discord_targets = {}

# Setup logger
logger = setup_logger("forwarder", "forwarder.log")


class MessageForwarder:
    """Forwards messages from queues to Discord"""

    def __init__(self):
        self.queue_base = Path(settings["paths"]["queue"])
        self.archive_base = Path(settings["paths"]["archive"])
        self.batch_size = settings["forwarder"]["batch_size"]
        self.max_retries = settings["forwarder"]["max_retries"]
        self.retry_backoff = settings["forwarder"]["retry_backoff_seconds"]

        # Discord sender
        self.discord = DiscordSender(logger=logger)

        # Statistics
        self.messages_sent = 0
        self.errors = 0
        self.rate_limits = 0
        self.start_time = datetime.now()

    def should_use_ocr(self, queue_name: str) -> bool:
        """Check if OCR should be used for this queue"""
        ocr_config = settings.get("ocr", {})
        if not ocr_config.get("enabled", False):
            return False

        ocr_queues = ocr_config.get("queues", [])
        return queue_name in ocr_queues

    def forward_message(self, message_path: str, queue_config: dict, queue_name: str) -> bool:
        """
        Forward a single message to Discord

        Args:
            message_path: Path to message JSON
            queue_config: Discord target configuration
            queue_name: Name of the queue for OCR checking

        Returns:
            True if successfully sent
        """
        try:
            # Read message
            data = read_json(message_path)

            # Determine if OCR should be used
            use_ocr = self.should_use_ocr(queue_name)

            # Get media path if exists
            media_path = data.get("media_path")
            if media_path and not Path(media_path).exists():
                logger.warning(f"Media file not found: {media_path}")
                media_path = None

            # Process based on OCR settings
            if use_ocr and media_path:
                # FREE path: OCR + formatter (text only, no image)
                try:
                    ocr_text = extract_text_from_image(media_path)
                    original_text = data.get("text", "")

                    # Format with AI picks parser
                    label = f"{data.get('chat_title', 'Unknown')}"
                    content = format_clean_picks(label, original_text, ocr_text or "")

                    # Clear media path - don't send image for free queues with OCR
                    media_path = None
                    logger.debug(f"Using OCR for {queue_name} - text only")

                except Exception as e:
                    logger.warning(f"OCR processing failed, using original: {e}")
                    # Fall back to original format
                    content = self.discord.format_telegram_message(data)
            else:
                # PAID path: Original image + text (no OCR)
                content = self.discord.format_telegram_message(data)
                logger.debug(f"Using original format for {queue_name}")

            # Send based on transport type
            transport = queue_config.get("transport", "bot")

            try:
                if transport == "webhook":
                    webhook_env = queue_config.get("webhook_env")
                    if not webhook_env:
                        raise ValueError(f"Missing webhook_env in config")
                    self.discord.send_webhook(webhook_env, content, media_path)

                else:  # bot transport
                    channel_id = str(queue_config.get("channel_id"))
                    if not channel_id:
                        raise ValueError(f"Missing channel_id in config")
                    self.discord.send_bot_message(channel_id, content, media_path)

                # Archive on success
                queue_name = Path(message_path).parent.name
                archive_path = archive_message(message_path, queue_name)
                logger.info(f"Sent and archived: {Path(message_path).name}")
                logger.debug(f"Archive: {archive_path}")

                self.messages_sent += 1
                return True

            except RateLimitException as e:
                self.rate_limits += 1
                log_rate_limit(logger, 429, e.retry_after)
                time.sleep(e.retry_after)
                return False

            except Exception as e:
                if "Missing Access" in str(e) or "403" in str(e):
                    logger.error(f"Missing Access to channel in {queue_config}")
                    logger.info("Fix: Check bot permissions or re-invite bot")
                    # Don't retry permission errors
                    self.errors += 1
                    # Move to failed folder
                    failed_dir = self.queue_base / Path(message_path).parent.name / "failed"
                    failed_dir.mkdir(parents=True, exist_ok=True)
                    Path(message_path).rename(failed_dir / Path(message_path).name)
                    return False
                else:
                    raise

        except Exception as e:
            self.errors += 1
            log_exception(logger, e, f"forward_message({message_path})")
            return False

    def process_queue(self, queue_name: str) -> int:
        """
        Process messages from a specific queue

        Args:
            queue_name: Queue directory name

        Returns:
            Number of messages processed
        """
        queue_config = discord_targets.get(queue_name)
        if not queue_config:
            logger.warning(f"No Discord target configured for queue: {queue_name}")
            return 0

        queue_dir = self.queue_base / queue_name
        if not queue_dir.exists():
            return 0

        # Get pending messages
        messages = list_json_files(str(queue_dir))[:self.batch_size]

        if not messages:
            return 0

        processed = 0
        for message_path in messages:
            retries = 0
            while retries < self.max_retries:
                if self.forward_message(message_path, queue_config, queue_name):
                    processed += 1
                    break
                retries += 1
                if retries < self.max_retries:
                    wait_time = self.retry_backoff * (2 ** retries)
                    logger.debug(f"Retry {retries}/{self.max_retries} after {wait_time}s")
                    time.sleep(wait_time)
            else:
                logger.error(f"Failed to send after {self.max_retries} retries: {message_path}")

        return processed

    def log_statistics(self):
        """Log forwarder statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        uptime_hours = uptime / 3600

        logger.info("=" * 50)
        logger.info("Forwarder Statistics:")
        logger.info(f"  Messages sent: {self.messages_sent}")
        logger.info(f"  Errors: {self.errors}")
        logger.info(f"  Rate limits hit: {self.rate_limits}")
        logger.info(f"  Uptime: {uptime_hours:.2f} hours")
        log_health_check(logger, "forwarder", "healthy")
        logger.info("=" * 50)

    def run(self):
        """Main forwarder loop"""
        logger.info("=" * 60)
        logger.info("Discord Forwarder Starting")
        logger.info(f"Queue base: {self.queue_base}")
        logger.info(f"Archive base: {self.archive_base}")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Max retries: {self.max_retries}")
        logger.info(f"Configured targets: {len(discord_targets)}")
        logger.info("=" * 60)

        last_stats_time = time.time()
        stats_interval = 300  # Log stats every 5 minutes

        while True:
            try:
                total_processed = 0

                # Process each queue
                for queue_name in discord_targets.keys():
                    count = self.process_queue(queue_name)
                    if count > 0:
                        logger.debug(f"Queue {queue_name}: processed {count}")
                        total_processed += count

                # Periodic statistics
                if time.time() - last_stats_time > stats_interval:
                    self.log_statistics()
                    last_stats_time = time.time()

                # Sleep if no messages
                if total_processed == 0:
                    time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Forwarder stopped by user")
                break
            except Exception as e:
                log_exception(logger, e, "main loop")
                time.sleep(5)

        # Final statistics
        self.log_statistics()


def main():
    """Main entry point"""
    forwarder = MessageForwarder()
    try:
        forwarder.run()
    except KeyboardInterrupt:
        logger.info("Forwarder shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()