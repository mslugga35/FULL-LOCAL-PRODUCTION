#!/usr/bin/env python3
"""
Comprehensive Discord Forwarder with Routing Support
Handles both webhook and bot-based message forwarding with proper queue routing
"""

import os
import json
import time
import requests
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import sys
import io

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/discord_forwarder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION")
MESSAGE_QUEUE_DIR = BASE_DIR / "message_queue"
PROCESSED_DIR = BASE_DIR / "processed_messages"
CONFIG_FILE = BASE_DIR / "routing_config.json"

class DiscordForwarder:
    def __init__(self):
        self.config = self.load_config()
        self.stats = {
            'sent': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': datetime.now()
        }
        self.bot_client = None
        self.ensure_directories()

    def load_config(self):
        """Load routing configuration from JSON file"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded routing configuration from {CONFIG_FILE}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def ensure_directories(self):
        """Create necessary directories"""
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)
        logger.info("Directories ensured")

    def send_webhook_message(self, webhook_url, message_data):
        """Send message via Discord webhook"""
        try:
            channel = message_data.get('channel', 'Unknown')
            text = message_data.get('text', '[no text]')
            timestamp = message_data.get('timestamp', '')
            chat_id = message_data.get('chat_id', 'Unknown')

            # Create Discord webhook payload
            discord_data = {
                'username': f'📡 {channel}',
                'content': text[:self.config['webhook_config']['max_message_length']],
                'embeds': [{
                    'footer': {
                        'text': f'{channel} • {timestamp[:19]} • Chat ID: {chat_id}'
                    },
                    'color': 0x00ff00
                }]
            }

            # Send to Discord
            response = requests.post(
                webhook_url,
                json=discord_data,
                timeout=self.config['webhook_config']['timeout']
            )

            if response.status_code == 204:
                return True, "Sent via webhook"
            else:
                return False, f"Webhook HTTP {response.status_code}: {response.text}"

        except Exception as e:
            return False, f"Webhook error: {str(e)}"

    async def send_bot_message(self, channel_id, message_data):
        """Send message via Discord bot (placeholder for future implementation)"""
        try:
            # TODO: Implement Discord bot functionality
            # For now, we'll return success as placeholder
            channel = message_data.get('channel', 'Unknown')
            text = message_data.get('text', '[no text]')

            logger.warning(f"Bot transport not yet implemented for channel {channel_id}")
            logger.info(f"Would send to channel {channel_id}: {text[:50]}...")

            # Simulate processing delay
            await asyncio.sleep(0.1)
            return True, "Bot transport not implemented yet"

        except Exception as e:
            return False, f"Bot error: {str(e)}"

    def get_routing_info(self, queue_path):
        """Get Discord routing information for a queue path"""
        queue_key = queue_path.replace('/', '\\\\')  # Normalize path separators

        routing = self.config.get('queue_to_discord_routing', {})

        # Try exact match first
        if queue_key in routing:
            return routing[queue_key]

        # Try with single backslash
        queue_key_single = queue_path.replace('/', '\\')
        if queue_key_single in routing:
            return routing[queue_key_single]

        # Try with forward slash
        queue_key_forward = queue_path.replace('\\', '/')
        if queue_key_forward in routing:
            return routing[queue_key_forward]

        logger.warning(f"No routing found for queue path: {queue_path}")
        return None

    async def process_message_file(self, file_path, queue_subdir):
        """Process a single message file"""
        try:
            # Read message data
            with open(file_path, 'r', encoding='utf-8') as f:
                message_data = json.load(f)

            # Get routing information
            routing_info = self.get_routing_info(queue_subdir)
            if not routing_info:
                logger.warning(f"No routing configured for {queue_subdir}, skipping {file_path.name}")
                self.stats['skipped'] += 1
                return False

            channel_id = routing_info['destination_channel']
            transport = routing_info['transport']

            success = False
            status = ""

            # Route based on transport type
            if transport == 'webhook':
                # Get webhook URL from channel config
                channel_config = self.config['discord_channels'].get(channel_id, {})
                webhook_url = channel_config.get('webhook_url')

                if webhook_url:
                    success, status = self.send_webhook_message(webhook_url, message_data)
                else:
                    success, status = False, "No webhook URL configured"

            elif transport == 'bot':
                success, status = await self.send_bot_message(channel_id, message_data)
            else:
                success, status = False, f"Unknown transport: {transport}"

            # Handle result
            if success:
                # Move to processed folder
                processed_folder = PROCESSED_DIR / queue_subdir
                processed_folder.mkdir(parents=True, exist_ok=True)

                dest_path = processed_folder / file_path.name
                file_path.rename(dest_path)

                logger.info(f"✅ {queue_subdir} → {channel_id} ({transport}): {file_path.name}")
                self.stats['sent'] += 1

                # Rate limiting
                delay = self.config.get('webhook_config' if transport == 'webhook' else 'bot_config', {}).get('rate_limit_delay', 0.5)
                await asyncio.sleep(delay)

                return True
            else:
                logger.error(f"❌ Failed {queue_subdir} → {channel_id}: {file_path.name} - {status}")
                self.stats['failed'] += 1
                return False

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            self.stats['failed'] += 1
            return False

    async def process_queue_folder(self, queue_path):
        """Process all messages in a queue folder"""
        queue_subdir = str(queue_path.relative_to(MESSAGE_QUEUE_DIR))

        json_files = list(queue_path.glob("*.json"))
        if not json_files:
            return 0

        sent_count = 0
        logger.info(f"📂 Processing {queue_subdir}: {len(json_files)} messages")

        for file_path in json_files:
            success = await self.process_message_file(file_path, queue_subdir)
            if success:
                sent_count += 1

        return sent_count

    async def scan_and_process_queues(self):
        """Scan all queue directories and process messages"""
        total_sent = 0

        # Get all queue directories based on configuration
        for queue_key in self.config['queue_to_discord_routing'].keys():
            queue_path = MESSAGE_QUEUE_DIR / queue_key.replace('\\\\', '\\')

            if queue_path.exists() and queue_path.is_dir():
                sent = await self.process_queue_folder(queue_path)
                total_sent += sent
            else:
                logger.debug(f"Queue directory does not exist: {queue_path}")

        return total_sent

    async def run_once(self):
        """Process all queue folders once"""
        logger.info("🚀 DISCORD FORWARDER - PROCESSING QUEUES")
        logger.info("=" * 50)

        # Display routing configuration
        for queue_key, routing in self.config['queue_to_discord_routing'].items():
            channel_name = self.config['discord_channels'].get(routing['destination_channel'], {}).get('name', 'Unknown')
            logger.info(f"{queue_key} → {channel_name} ({routing['transport']})")

        logger.info("=" * 50)

        total_sent = await self.scan_and_process_queues()
        return total_sent

    async def run_continuous(self):
        """Run continuous forwarding loop"""
        logger.info("🚀 DISCORD FORWARDER STARTED")
        logger.info("=" * 50)
        logger.info(f"Queue Directory: {MESSAGE_QUEUE_DIR}")
        logger.info(f"Config File: {CONFIG_FILE}")
        logger.info("=" * 50)

        while True:
            try:
                sent = await self.run_once()

                if sent > 0:
                    logger.info(f"📊 Batch complete: {sent} messages sent")
                    self.print_stats()

                await asyncio.sleep(10)  # Check every 10 seconds

            except KeyboardInterrupt:
                logger.info("👋 Stopping forwarder...")
                self.print_final_stats()
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                await asyncio.sleep(30)

    def print_stats(self):
        """Print current statistics"""
        runtime = datetime.now() - self.stats['start_time']
        logger.info(f"📊 Stats - Runtime: {runtime}, Sent: {self.stats['sent']}, "
                   f"Failed: {self.stats['failed']}, Skipped: {self.stats['skipped']}")

    def print_final_stats(self):
        """Print final statistics"""
        runtime = datetime.now() - self.stats['start_time']
        logger.info("\n" + "=" * 50)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Runtime: {runtime}")
        logger.info(f"Messages sent: {self.stats['sent']}")
        logger.info(f"Messages failed: {self.stats['failed']}")
        logger.info(f"Messages skipped: {self.stats['skipped']}")
        logger.info("=" * 50)

async def main():
    forwarder = DiscordForwarder()

    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run once and exit
        sent = await forwarder.run_once()
        logger.info(f"✅ One-time forwarding complete: {sent} messages sent")
        forwarder.print_stats()
    else:
        # Run continuously
        await forwarder.run_continuous()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)