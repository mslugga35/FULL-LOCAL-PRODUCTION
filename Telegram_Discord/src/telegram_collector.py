#!/usr/bin/env python
"""
Telegram message collector - ingests messages from configured channels
"""
import asyncio
import sys
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger, log_exception, log_health_check
from src.utils.telegram_client import start_collector
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
    # Default settings if config doesn't exist
    settings = {
        "paths": {
            "logs": str(BASE_PATH / "logs"),
            "inbox": str(BASE_PATH / "inbox")
        },
        "collector": {
            "media_download": True
        }
    }

# Setup logger
logger = setup_logger("telegram_collector", "collector.log")


def get_monitored_channels():
    """Get list of channel IDs to monitor from routing map"""
    channels = list(ROUTING_MAP.keys())
    logger.info(f"Configured channels: {channels}")
    return channels


async def main():
    """Main collector entry point"""
    logger.info("=" * 60)
    logger.info("Telegram Collector Starting")
    logger.info("=" * 60)

    # Configuration
    inbox_dir = Path(settings["paths"]["inbox"])
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Get channels to monitor
    channels = get_monitored_channels()

    if not channels:
        logger.error("No channels configured in ROUTING_MAP")
        return

    # Check environment
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        logger.error("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in environment")
        logger.info("Please set these in your .env file")
        logger.info("You can generate a session with: python src/make_session.py")
        return

    # Log configuration
    logger.info(f"Inbox directory: {inbox_dir}")
    logger.info(f"Media download: {settings['collector']['media_download']}")
    logger.info(f"Monitoring {len(channels)} channels")

    try:
        # Start collector
        await start_collector(
            chat_ids=channels,
            inbox_dir=str(inbox_dir),
            media_download=settings["collector"]["media_download"],
            logger=logger
        )
    except KeyboardInterrupt:
        logger.info("Collector stopped by user")
    except Exception as e:
        log_exception(logger, e, "main")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Telegram collector shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)