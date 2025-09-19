#!/usr/bin/env python3
"""
Production Discord Forwarder
Reads from routing_config.json and implements exact routing specified.
Handles both webhook and bot transport methods with proper rate limiting and error handling.
"""

import asyncio
import json
import logging
import os
import time
import aiohttp
import discord
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/discord_forwarder_production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DiscordForwarderProduction:
    def __init__(self):
        self.config = self.load_config()
        self.bot_client = None
        self.processed_files = set()
        self.running = False

        # Load environment variables
        self.load_environment()

        # Rate limiting
        self.last_webhook_send = {}
        self.last_bot_send = {}

        # Initialize Discord bot client
        self.initialize_bot_client()

    def load_environment(self):
        """Load environment variables from .env file"""
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

        self.bot_token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")

    def load_config(self) -> Dict[str, Any]:
        """Load routing configuration from JSON file"""
        config_path = Path('routing_config.json')
        if not config_path.exists():
            raise FileNotFoundError("routing_config.json not found")

        with open(config_path, 'r') as f:
            config = json.load(f)

        logger.info("Loaded routing configuration successfully")
        return config

    def initialize_bot_client(self):
        """Initialize Discord bot client"""
        intents = discord.Intents.default()
        intents.message_content = True

        self.bot_client = discord.Client(intents=intents)

        @self.bot_client.event
        async def on_ready():
            logger.info(f'Bot logged in as {self.bot_client.user}')

        @self.bot_client.event
        async def on_error(event, *args, **kwargs):
            logger.error(f'Discord client error in {event}: {args} {kwargs}')

    async def send_webhook_message(self, webhook_url: str, content: str, username: str = None) -> bool:
        """Send message via Discord webhook"""
        try:
            # Rate limiting for webhooks
            current_time = time.time()
            webhook_delay = self.config.get('webhook_config', {}).get('rate_limit_delay', 0.5)

            if webhook_url in self.last_webhook_send:
                time_diff = current_time - self.last_webhook_send[webhook_url]
                if time_diff < webhook_delay:
                    await asyncio.sleep(webhook_delay - time_diff)

            # Truncate message if too long
            max_length = self.config.get('webhook_config', {}).get('max_message_length', 2000)
            if len(content) > max_length:
                content = content[:max_length-3] + "..."
                logger.warning(f"Message truncated to {max_length} characters")

            # Prepare webhook payload
            payload = {'content': content}
            if username:
                payload['username'] = username

            # Send webhook request
            timeout = self.config.get('webhook_config', {}).get('timeout', 10)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        self.last_webhook_send[webhook_url] = time.time()
                        logger.info(f"Webhook message sent successfully")
                        return True
                    else:
                        logger.error(f"Webhook failed with status {response.status}: {await response.text()}")
                        return False

        except Exception as e:
            logger.error(f"Error sending webhook message: {e}")
            return False

    async def send_bot_message(self, channel_id: str, content: str) -> bool:
        """Send message via Discord bot"""
        try:
            if not self.bot_client or not self.bot_client.is_ready():
                logger.error("Bot client not ready")
                return False

            # Rate limiting for bot messages
            current_time = time.time()
            bot_delay = self.config.get('bot_config', {}).get('rate_limit_delay', 0.5)

            if channel_id in self.last_bot_send:
                time_diff = current_time - self.last_bot_send[channel_id]
                if time_diff < bot_delay:
                    await asyncio.sleep(bot_delay - time_diff)

            # Truncate message if too long
            max_length = self.config.get('bot_config', {}).get('max_message_length', 2000)
            if len(content) > max_length:
                content = content[:max_length-3] + "..."
                logger.warning(f"Message truncated to {max_length} characters")

            # Get channel and send message
            channel = self.bot_client.get_channel(int(channel_id))
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return False

            await channel.send(content)
            self.last_bot_send[channel_id] = time.time()
            logger.info(f"Bot message sent to channel {channel_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending bot message: {e}")
            return False

    def scan_queue_directories(self) -> List[Path]:
        """Scan all queue directories for JSON files to process"""
        message_queue_dir = Path('message_queue')
        if not message_queue_dir.exists():
            logger.warning("message_queue directory not found")
            return []

        json_files = []

        # Get all routing configurations
        for queue_dir, routing_config in self.config['queue_to_discord_routing'].items():
            queue_path = message_queue_dir / queue_dir

            if queue_path.exists():
                # Find all JSON files in this queue directory
                for json_file in queue_path.glob('*.json'):
                    if json_file.name not in self.processed_files:
                        json_files.append(json_file)
                        logger.debug(f"Found unprocessed file: {json_file}")

        return sorted(json_files, key=lambda x: x.stat().st_mtime)

    def load_message_from_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load message data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                message_data = json.load(f)
            return message_data
        except Exception as e:
            logger.error(f"Error loading message from {file_path}: {e}")
            return None

    def get_routing_for_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get routing configuration for a specific file based on its path"""
        message_queue_dir = Path('message_queue')

        # Get relative path from message_queue directory
        try:
            relative_path = file_path.parent.relative_to(message_queue_dir)
            queue_dir = str(relative_path).replace('/', '\\')  # Convert to Windows path format

            # Look up routing configuration
            routing_config = self.config['queue_to_discord_routing'].get(queue_dir)
            if routing_config:
                logger.debug(f"Found routing for {queue_dir}: {routing_config}")
                return routing_config
            else:
                logger.warning(f"No routing configuration found for {queue_dir}")
                return None

        except Exception as e:
            logger.error(f"Error determining routing for {file_path}: {e}")
            return None

    def format_message_content(self, message_data: Dict[str, Any]) -> str:
        """Format message content for Discord"""
        try:
            # Extract relevant fields
            text = message_data.get('text', '')
            sender_name = message_data.get('sender_name', 'Unknown')
            date = message_data.get('date', '')

            # Format timestamp if available
            formatted_date = ""
            if date:
                try:
                    if isinstance(date, str):
                        # Try to parse and reformat
                        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                    else:
                        formatted_date = str(date)
                except:
                    formatted_date = str(date)

            # Build message content
            content_parts = []

            if sender_name and sender_name != 'Unknown':
                content_parts.append(f"**{sender_name}**")

            if formatted_date:
                content_parts.append(f"*{formatted_date}*")

            if text:
                content_parts.append(text)

            content = '\n'.join(content_parts)

            # Fallback to raw text if no content
            if not content.strip():
                content = str(message_data)

            return content

        except Exception as e:
            logger.error(f"Error formatting message content: {e}")
            return str(message_data)

    async def process_message_file(self, file_path: Path) -> bool:
        """Process a single message file"""
        try:
            logger.info(f"Processing file: {file_path}")

            # Load message data
            message_data = self.load_message_from_file(file_path)
            if not message_data:
                return False

            # Get routing configuration
            routing_config = self.get_routing_for_file(file_path)
            if not routing_config:
                logger.warning(f"No routing found for {file_path}, skipping")
                return False

            # Format message content
            content = self.format_message_content(message_data)
            if not content.strip():
                logger.warning(f"Empty content for {file_path}, skipping")
                return False

            # Determine transport method
            transport = routing_config['transport']
            destination_channel = routing_config['destination_channel']

            success = False

            if transport == 'webhook':
                # Use webhook transport
                webhook_url = self.config['discord_channels'][destination_channel].get('webhook_url')
                if webhook_url:
                    success = await self.send_webhook_message(
                        webhook_url,
                        content,
                        username="Telegram Forwarder"
                    )
                else:
                    logger.error(f"No webhook URL found for channel {destination_channel}")

            elif transport == 'bot':
                # Use bot transport
                success = await self.send_bot_message(destination_channel, content)

            else:
                logger.error(f"Unknown transport method: {transport}")

            if success:
                # Mark file as processed
                self.processed_files.add(file_path.name)

                # Move file to processed directory
                processed_dir = Path('processed_messages')
                processed_dir.mkdir(exist_ok=True)

                # Create subdirectory structure
                relative_path = file_path.parent.relative_to(Path('message_queue'))
                target_dir = processed_dir / relative_path
                target_dir.mkdir(parents=True, exist_ok=True)

                # Move file
                target_path = target_dir / file_path.name
                file_path.rename(target_path)

                logger.info(f"Successfully processed and moved {file_path} to {target_path}")
                return True
            else:
                logger.error(f"Failed to send message from {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False

    async def run_processing_cycle(self):
        """Run one cycle of message processing"""
        try:
            # Scan for files to process
            files_to_process = self.scan_queue_directories()

            if not files_to_process:
                logger.debug("No files to process")
                return

            logger.info(f"Found {len(files_to_process)} files to process")

            # Process each file
            processed_count = 0
            for file_path in files_to_process:
                success = await self.process_message_file(file_path)
                if success:
                    processed_count += 1

                # Small delay between files to avoid overwhelming Discord
                await asyncio.sleep(0.1)

            logger.info(f"Processing cycle complete: {processed_count}/{len(files_to_process)} files processed successfully")

        except Exception as e:
            logger.error(f"Error in processing cycle: {e}")

    async def start_bot_client(self):
        """Start the Discord bot client"""
        try:
            await self.bot_client.start(self.bot_token)
        except Exception as e:
            logger.error(f"Error starting bot client: {e}")

    async def main_loop(self):
        """Main processing loop"""
        logger.info("Starting Discord Forwarder Production")

        # Create logs directory
        Path('logs').mkdir(exist_ok=True)

        self.running = True

        # Start bot client in background
        bot_task = asyncio.create_task(self.start_bot_client())

        # Wait for bot to be ready
        while not self.bot_client.is_ready():
            await asyncio.sleep(1)

        logger.info("Bot client ready, starting processing loop")

        try:
            while self.running:
                await self.run_processing_cycle()

                # Wait before next cycle
                await asyncio.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.running = False
            if self.bot_client:
                await self.bot_client.close()
            logger.info("Discord Forwarder Production stopped")

    def stop(self):
        """Stop the forwarder"""
        self.running = False

def main():
    """Main entry point"""
    try:
        forwarder = DiscordForwarderProduction()
        asyncio.run(forwarder.main_loop())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()