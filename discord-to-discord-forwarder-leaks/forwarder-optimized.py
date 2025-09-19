#!/usr/bin/env python3
"""
Discord Multi-Channel Forwarder - PRODUCTION VERSION
Forwards messages from Server 1 channels to Server 2 channels via webhooks
"""

import asyncio
import json
import logging
import aiohttp
from datetime import datetime, timezone
import sys
import os

# Configure logging - suppress Unicode errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forwarder.log', encoding='utf-8')
    ]
)

# Add safe console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
console_handler.setLevel(logging.INFO)

# Override emit to handle Unicode errors gracefully
original_emit = console_handler.emit
def safe_emit(record):
    try:
        original_emit(record)
    except UnicodeEncodeError:
        # Skip logging messages with Unicode issues to console (still logs to file)
        pass
console_handler.emit = safe_emit

logging.getLogger().addHandler(console_handler)
logger = logging.getLogger(__name__)

class DiscordForwarder:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.user_token = self.config['user_token']
        self.channel_mappings = self.config['channel_mappings']
        self.fetch_history = self.config.get('fetch_history_on_start', False)
        self.session = None
        self.last_message_ids = self.load_last_messages()
        self.stats = {'messages_forwarded': 0, 'errors': 0, 'start_time': datetime.now()}
    
    def load_last_messages(self):
        """Load last message IDs from file to prevent duplicates on restart"""
        try:
            if os.path.exists('last_messages.json'):
                with open('last_messages.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not load last messages: {e}")
        return {}
    
    def save_last_messages(self):
        """Save last message IDs to file"""
        try:
            with open('last_messages.json', 'w') as f:
                json.dump(self.last_message_ids, f)
        except Exception as e:
            logger.debug(f"Could not save last messages: {e}")
        
    async def start(self):
        """Start the forwarder"""
        self.session = aiohttp.ClientSession()
        logger.info("=" * 50)
        logger.info("Discord Forwarder Started")
        logger.info(f"Monitoring {len(self.channel_mappings)} channels")
        logger.info("=" * 50)
        
        try:
            # Optional: Fetch today's history on first run
            if self.fetch_history:
                logger.info("Loading today's message history...")
                await self.fetch_todays_messages()
                logger.info("History loaded. Starting live monitoring...")
            else:
                logger.info("Starting live monitoring (no history fetch)...")
            
            # Monitor for new messages with very conservative rate limiting
            while True:
                for source_channel, webhook_url in self.channel_mappings.items():
                    await self.check_new_messages(source_channel, webhook_url)
                    await asyncio.sleep(10)  # Wait 10 seconds between each channel check
                logger.info("Full cycle completed, waiting 300 seconds...")
                await asyncio.sleep(300)  # Wait 5 minutes before next full cycle
                
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            await self.cleanup()
    
    async def fetch_todays_messages(self):
        """Fetch today's messages (optional, for first run)"""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        for source_channel, webhook_url in self.channel_mappings.items():
            try:
                headers = {'Authorization': self.user_token, 'Content-Type': 'application/json'}
                url = f'https://discord.com/api/v10/channels/{source_channel}/messages'
                params = {'limit': 100}
                
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        messages = await response.json()
                        
                        # Filter and forward today's messages
                        todays_messages = []
                        for msg in messages:
                            msg_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                            if msg_time >= today:
                                todays_messages.append(msg)
                        
                        if todays_messages:
                            logger.info(f"Channel {source_channel}: Found {len(todays_messages)} messages from today")
                            for message in reversed(todays_messages):
                                await self.forward_message(message, webhook_url)
                                await asyncio.sleep(0.5)
                        
                        # Set last message ID
                        if messages:
                            self.last_message_ids[source_channel] = messages[0]['id']
                            
            except Exception as e:
                logger.error(f"Error fetching history for {source_channel}: {e}")
    
    async def check_new_messages(self, source_channel, webhook_url):
        """Check for new messages in a channel"""
        try:
            headers = {'Authorization': self.user_token, 'Content-Type': 'application/json'}
            url = f'https://discord.com/api/v10/channels/{source_channel}/messages'
            params = {'limit': 10}
            
            if source_channel in self.last_message_ids:
                params['after'] = self.last_message_ids[source_channel]
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    messages = await response.json()
                    
                    # Process new messages
                    for message in reversed(messages):
                        await self.forward_message(message, webhook_url)
                        self.last_message_ids[source_channel] = message['id']
                        self.save_last_messages()  # Save after each forward to prevent duplicates
                        
                elif response.status == 429:
                    retry_after = float(response.headers.get('X-RateLimit-Retry-After', 5))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
        except Exception as e:
            logger.debug(f"Check error for {source_channel}: {e}")
    
    async def forward_message(self, message, webhook_url):
        """Forward a message to webhook with rate limiting"""
        # Add small delay to prevent webhook rate limits
        await asyncio.sleep(0.5)  # 500ms delay between webhook posts

        try:
            author = message.get('author', {})
            username = author.get('username', 'Unknown')
            
            # Format message
            timestamp = message.get('timestamp', '')
            time_str = ""
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%I:%M %p')
            
            content = message.get('content', '')
            
            # Remove @everyone and @here mentions to prevent notifications
            content = content.replace('@everyone', '`@everyone`')
            content = content.replace('@here', '`@here`')
            
            # Only forward if there's content or attachments
            if content or message.get('attachments') or message.get('embeds'):
                webhook_data = {
                    'content': f"[{time_str}] {content}",
                    'username': username,
                    'avatar_url': self.get_avatar_url(author)
                }
                
                # Add embeds
                if message.get('embeds'):
                    webhook_data['embeds'] = message['embeds'][:10]
                
                # Add attachments
                if message.get('attachments'):
                    att_text = '\n**Files:**\n'
                    for att in message['attachments']:
                        att_text += f"• [{att.get('filename', 'file')}]({att.get('url', '')})\n"
                    webhook_data['content'] = (webhook_data['content'] + att_text)[:2000]
                
                # Send to webhook
                async with self.session.post(webhook_url, json=webhook_data) as response:
                    if response.status == 204:
                        self.stats['messages_forwarded'] += 1
                        logger.info(f"Forwarded: {username} - {content[:50]}...")
                    else:
                        logger.error(f"Webhook error: {response.status}")
                        self.stats['errors'] += 1
                        
        except Exception as e:
            logger.error(f"Forward error: {e}")
            self.stats['errors'] += 1
    
    def get_avatar_url(self, author):
        """Get user avatar URL"""
        if not author.get('avatar'):
            return None
        user_id = author.get('id')
        avatar_hash = author['avatar']
        ext = 'gif' if avatar_hash.startswith('a_') else 'png'
        return f'https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}'
    
    async def cleanup(self):
        """Cleanup on shutdown"""
        if self.session:
            await self.session.close()
        
        runtime = datetime.now() - self.stats['start_time']
        logger.info("=" * 50)
        logger.info(f"Forwarder stopped")
        logger.info(f"Runtime: {runtime}")
        logger.info(f"Messages forwarded: {self.stats['messages_forwarded']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 50)

async def main():
    forwarder = DiscordForwarder('config.json')
    await forwarder.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)