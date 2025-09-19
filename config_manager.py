#!/usr/bin/env python3
"""
Master Configuration Manager - Single source of truth for Telegram to Discord routing
Provides unified configuration loading and helper functions for the entire pipeline
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import io

# Force UTF-8 on Windows - more compatible approach
if sys.platform == "win32":
    import locale
    if locale.getpreferredencoding().upper() != 'UTF-8':
        os.environ['PYTHONIOENCODING'] = 'utf-8'

class ConfigurationManager:
    """Unified configuration management for the Telegram to Discord routing system"""

    def __init__(self, config_path: str = None):
        """Initialize the configuration manager"""
        if config_path is None:
            config_path = Path(__file__).parent / "routing_config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.base_path = Path(self.config.get('windows_base_path', r'C:\Users\mpmmo\message_queue'))

        # Initialize paths
        self.recent_messages_dir = Path(__file__).parent / "recent_messages"
        self.message_queue_dir = Path(__file__).parent / "message_queue"
        self.processed_dir = Path(__file__).parent / "processed_messages"
        self.sent_archive_dir = Path(__file__).parent / "sent_archive"

        # Discord webhooks and channel configurations
        # ONLY for paid channels - FREE channels should use bot transport
        self.paid_server_webhook = 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN'

        # Validate configuration
        self._validate_config()

        print(f"[OK] Configuration loaded: {len(self.config.get('telegram_channels', {}))} channels configured")

    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise Exception(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in configuration file: {e}")

    def _validate_config(self):
        """Validate configuration completeness"""
        required_keys = ['telegram_channels', 'discord_forwarder_integration', 'queue_management']

        for key in required_keys:
            if key not in self.config:
                raise Exception(f"Missing required configuration key: {key}")

        # Validate channel configurations
        for channel_id, channel_config in self.config['telegram_channels'].items():
            required_channel_keys = ['name', 'queue_path', 'type', 'enabled']
            for key in required_channel_keys:
                if key not in channel_config:
                    raise Exception(f"Missing required key '{key}' in channel {channel_id}")

    def get_all_channels(self) -> Dict[str, Dict]:
        """Get all configured Telegram channels"""
        return self.config.get('telegram_channels', {})

    def get_enabled_channels(self) -> Dict[str, Dict]:
        """Get only enabled Telegram channels"""
        channels = self.get_all_channels()
        return {cid: config for cid, config in channels.items() if config.get('enabled', False)}

    def get_channel_by_id(self, channel_id: str) -> Optional[Dict]:
        """Get channel configuration by Telegram channel ID"""
        return self.config.get('telegram_channels', {}).get(str(channel_id))

    def get_channel_by_name(self, channel_name: str) -> Optional[Dict]:
        """Get channel configuration by channel name (fuzzy match)"""
        channels = self.get_all_channels()

        # Try exact match first
        for channel_config in channels.values():
            if channel_config.get('name', '').lower() == channel_name.lower():
                return channel_config
            if channel_config.get('display_name', '').lower() == channel_name.lower():
                return channel_config

        # Try partial match
        channel_lower = channel_name.lower()
        for channel_config in channels.values():
            if channel_lower in channel_config.get('name', '').lower():
                return channel_config
            if channel_lower in channel_config.get('display_name', '').lower():
                return channel_config

        return None

    def determine_queue_folder(self, message_data: Dict) -> Optional[str]:
        """Determine which queue folder a message should go to based on message data"""
        channel_name = message_data.get('channel', '').strip()
        channel_id = str(message_data.get('chat_id', ''))

        # Try by channel ID first (most reliable)
        if channel_id:
            channel_config = self.get_channel_by_id(channel_id)
            if channel_config and channel_config.get('enabled', False):
                return channel_config.get('queue_path')

        # Try by channel name
        if channel_name:
            channel_config = self.get_channel_by_name(channel_name)
            if channel_config and channel_config.get('enabled', False):
                return channel_config.get('queue_path')

        # Try to find channel by text content keywords
        text = message_data.get('text', '').lower()
        for channel_config in self.get_enabled_channels().values():
            channel_name_lower = channel_config.get('name', '').lower()
            if channel_name_lower in text:
                return channel_config.get('queue_path')

        return None

    def get_delivery_config(self, queue_folder: str) -> Optional[Dict]:
        """Get Discord delivery configuration for a queue folder"""
        # Find the channel configuration that uses this queue folder
        for channel_config in self.get_enabled_channels().values():
            if channel_config.get('queue_path') == queue_folder:
                delivery_config = {
                    'queue_folder': queue_folder,
                    'channel_type': channel_config.get('type'),
                    'discord_server': channel_config.get('discord_server'),
                    'discord_channel': channel_config.get('discord_channel'),
                    'delivery_method': channel_config.get('delivery_method', 'bot')
                }

                # Add webhook URL for paid channels
                if channel_config.get('delivery_method') == 'webhook':
                    delivery_config['webhook_url'] = self.paid_server_webhook

                return delivery_config

        return None

    def get_all_queue_folders(self) -> List[str]:
        """Get list of all queue folders that should exist"""
        folders = set()
        for channel_config in self.get_enabled_channels().values():
            queue_path = channel_config.get('queue_path')
            if queue_path:
                folders.add(queue_path)
        return sorted(list(folders))

    def ensure_directories(self):
        """Create all necessary directories"""
        directories = [
            self.recent_messages_dir,
            self.message_queue_dir,
            self.processed_dir,
            self.sent_archive_dir
        ]

        # Create main directories
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        # Create queue subdirectories
        queue_folders = self.get_all_queue_folders()
        for folder in queue_folders:
            queue_path = self.message_queue_dir / folder
            queue_path.mkdir(parents=True, exist_ok=True)

            # Create processed subdirectory
            processed_path = self.processed_dir / folder
            processed_path.mkdir(parents=True, exist_ok=True)

        print(f"[OK] Directories ensured: {len(queue_folders)} queue folders")
        return queue_folders

    def add_routing_metadata(self, message_data: Dict, queue_folder: str) -> Dict:
        """Add routing metadata to message data"""
        message_data['routing_metadata'] = {
            'routed_from': 'recent_messages',
            'routed_to': queue_folder,
            'routed_at': datetime.now().isoformat(),
            'config_version': self.config.get('version', '1.0'),
            'routing_config': self.get_delivery_config(queue_folder)
        }
        return message_data

    def format_discord_message(self, message_data: Dict) -> Dict:
        """Format message data for Discord delivery"""
        channel = message_data.get('channel', 'Unknown Channel')
        text = message_data.get('text', '[no text]')
        timestamp = message_data.get('timestamp', '')

        # Get routing info
        routing_meta = message_data.get('routing_metadata', {})
        queue_folder = routing_meta.get('routed_to', 'unknown')

        # Create Discord webhook payload
        discord_data = {
            'username': f'📡 {channel}',
            'content': text[:2000],  # Discord character limit
            'embeds': [{
                'footer': {
                    'text': f'{channel} • {timestamp[:19]} • via {queue_folder}'
                },
                'color': self._get_embed_color(queue_folder)
            }]
        }

        return discord_data

    def _get_embed_color(self, queue_folder: str) -> int:
        """Get Discord embed color based on queue folder type"""
        if 'paid' in queue_folder:
            return 0xFFD700  # Gold for paid
        elif 'free' in queue_folder:
            return 0x00FF00  # Green for free
        elif 'leaked' in queue_folder:
            return 0xFF4500  # Orange for leaked
        elif 'exclusive' in queue_folder:
            return 0x9932CC  # Purple for exclusive
        else:
            return 0x36393F  # Default Discord color

    def get_processing_stats(self) -> Dict:
        """Get current processing statistics"""
        stats = {
            'recent_messages_count': 0,
            'queue_folders': {},
            'processed_folders': {},
            'total_queued': 0,
            'total_processed': 0
        }

        # Count recent messages
        if self.recent_messages_dir.exists():
            stats['recent_messages_count'] = len(list(self.recent_messages_dir.glob('*.json')))

        # Count messages in each queue folder
        for folder in self.get_all_queue_folders():
            queue_path = self.message_queue_dir / folder
            processed_path = self.processed_dir / folder

            if queue_path.exists():
                queue_count = len(list(queue_path.glob('*.json')))
                stats['queue_folders'][folder] = queue_count
                stats['total_queued'] += queue_count

            if processed_path.exists():
                processed_count = len(list(processed_path.glob('*.json')))
                stats['processed_folders'][folder] = processed_count
                stats['total_processed'] += processed_count

        return stats

    def print_system_status(self):
        """Print comprehensive system status"""
        print("\n" + "=" * 60)
        print("CONFIGURATION SYSTEM STATUS")
        print("=" * 60)

        # Configuration info
        print(f"Config Version: {self.config.get('version', 'Unknown')}")
        print(f"Base Path: {self.base_path}")
        print(f"Config Date: {self.config.get('created', 'Unknown')}")

        # Channel info
        channels = self.get_all_channels()
        enabled_channels = self.get_enabled_channels()
        print(f"Channels: {len(enabled_channels)}/{len(channels)} enabled")

        # Queue folders
        queue_folders = self.get_all_queue_folders()
        print(f"Queue Folders: {len(queue_folders)}")
        for folder in queue_folders:
            delivery_config = self.get_delivery_config(folder)
            if delivery_config:
                method = delivery_config.get('delivery_method', 'unknown')
                channel_type = delivery_config.get('channel_type', 'unknown')
                print(f"   - {folder} -> {channel_type} via {method}")

        # Processing stats
        stats = self.get_processing_stats()
        print(f"Messages: {stats['recent_messages_count']} recent, {stats['total_queued']} queued, {stats['total_processed']} processed")

        print("=" * 60)

    def reload_config(self):
        """Reload configuration from file"""
        old_version = self.config.get('version', 'unknown')
        self.config = self._load_config()
        self._validate_config()
        new_version = self.config.get('version', 'unknown')
        print(f"Configuration reloaded: {old_version} -> {new_version}")
        return True

def main():
    """Test the configuration manager"""
    try:
        config_manager = ConfigurationManager()
        config_manager.print_system_status()

        # Test directory creation
        folders = config_manager.ensure_directories()
        print(f"\n[OK] Test complete: {len(folders)} queue folders ensured")

    except Exception as e:
        print(f"[ERROR] Configuration error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())