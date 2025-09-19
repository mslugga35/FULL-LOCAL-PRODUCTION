#!/usr/bin/env python
"""
Message router - moves messages from inbox to appropriate queue directories
"""
import os
import sys
import json
import time
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger, log_exception, log_health_check
from src.utils.fs import read_json, move, list_json_files, get_queue_backlog
from config.channel_routing_map import ROUTING_MAP


# Load environment variables
BASE_PATH = Path("C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord")
load_dotenv(BASE_PATH / ".env")

# Load settings
settings_path = BASE_PATH / "config" / "settings.yaml"
if settings_path.exists():
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = yaml.safe_load(f)
else:
    # Default settings
    settings = {
        "paths": {
            "logs": str(BASE_PATH / "logs"),
            "inbox": str(BASE_PATH / "inbox"),
            "queue": str(BASE_PATH / "message_queue")
        },
        "router": {
            "poll_interval": 2,
            "batch_size": 10
        }
    }

# Setup logger
logger = setup_logger("router", "router.log")


class MessageRouter:
    """Routes messages from inbox to appropriate queues"""

    def __init__(self):
        self.inbox_dir = Path(settings["paths"]["inbox"])
        self.queue_base = Path(settings["paths"]["queue"])
        self.poll_interval = settings.get("router", {}).get("poll_interval", 2)
        self.batch_size = settings.get("router", {}).get("batch_size", 10)

        # Statistics
        self.messages_routed = 0
        self.errors = 0
        self.start_time = datetime.now()

    def route_message(self, message_path: str) -> bool:
        """
        Route a single message to appropriate queue

        Args:
            message_path: Path to message JSON file

        Returns:
            True if successfully routed
        """
        try:
            # Read message
            data = read_json(message_path)
            chat_id = int(data.get("chat_id", 0))

            # Find queue
            queue_name = ROUTING_MAP.get(chat_id)
            if not queue_name:
                logger.warning(f"No route for chat_id={chat_id} from {Path(message_path).name}")
                # Move to unrouted folder
                unrouted_dir = self.queue_base / "unrouted"
                unrouted_dir.mkdir(parents=True, exist_ok=True)
                move(message_path, str(unrouted_dir))
                return False

            # Route to queue
            queue_dir = self.queue_base / queue_name
            queue_dir.mkdir(parents=True, exist_ok=True)

            new_path = move(message_path, str(queue_dir))
            logger.info(f"Routed: {Path(message_path).name} → {queue_name}")
            logger.debug(f"New path: {new_path}")

            self.messages_routed += 1
            return True

        except Exception as e:
            self.errors += 1
            log_exception(logger, e, f"route_message({message_path})")

            # Move to error folder
            try:
                error_dir = self.queue_base / "errors"
                error_dir.mkdir(parents=True, exist_ok=True)
                move(message_path, str(error_dir))
            except:
                pass

            return False

    def process_batch(self) -> int:
        """
        Process a batch of messages from inbox

        Returns:
            Number of messages processed
        """
        # Get pending messages
        messages = list_json_files(str(self.inbox_dir))[:self.batch_size]

        if not messages:
            return 0

        processed = 0
        for message_path in messages:
            if self.route_message(message_path):
                processed += 1

        return processed

    def log_statistics(self):
        """Log router statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        uptime_hours = uptime / 3600

        logger.info("=" * 50)
        logger.info("Router Statistics:")
        logger.info(f"  Messages routed: {self.messages_routed}")
        logger.info(f"  Errors: {self.errors}")
        logger.info(f"  Uptime: {uptime_hours:.2f} hours")

        # Queue backlogs
        for queue_name in ROUTING_MAP.values():
            backlog = get_queue_backlog(queue_name)
            if backlog > 0:
                logger.info(f"  Queue {queue_name}: {backlog} pending")

        log_health_check(logger, "router", "healthy")
        logger.info("=" * 50)

    def run(self):
        """Main router loop"""
        logger.info("=" * 60)
        logger.info("Message Router Starting")
        logger.info(f"Inbox: {self.inbox_dir}")
        logger.info(f"Queue base: {self.queue_base}")
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Configured routes: {len(ROUTING_MAP)}")
        logger.info("=" * 60)

        last_stats_time = time.time()
        stats_interval = 300  # Log stats every 5 minutes

        while True:
            try:
                # Process batch
                count = self.process_batch()
                if count > 0:
                    logger.debug(f"Processed {count} messages")

                # Periodic statistics
                if time.time() - last_stats_time > stats_interval:
                    self.log_statistics()
                    last_stats_time = time.time()

                # Sleep if no messages
                if count == 0:
                    time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("Router stopped by user")
                break
            except Exception as e:
                log_exception(logger, e, "main loop")
                time.sleep(5)  # Longer sleep on error

        # Final statistics
        self.log_statistics()


def main():
    """Main entry point"""
    router = MessageRouter()
    try:
        router.run()
    except KeyboardInterrupt:
        logger.info("Router shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()