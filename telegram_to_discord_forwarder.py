#!/usr/bin/env python3
"""
Telegram to Discord Forwarder - Routes Telegram messages to correct Discord servers
Server 675908407617650697: UATB, Diamond/Chamba (paid)
Server 1390050801136701642: Free/Leaked cappers
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
import sys
import io

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Paths
MESSAGE_QUEUE_DIR = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\message_queue")
PROCESSED_DIR = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\processed_messages")

# Discord Webhook URLs
# Server 675908407617650697 - Paid Server (UATB, Diamond)
PAID_SERVER_WEBHOOK = 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN'

# Server 1390050801136701642 - Free/Leaks Server
# These will use bot transport instead of webhooks
FREE_SERVER_CHANNELS = {
    'free_cappers': '1403894557615325216',    # Cappers Free channel
    'cappers_leaked': '1403894596186017962',  # Cappers Leaked channel
    'exclusive_cappers': '1403894653660692500' # Exclusive Cappers channel
}

# Folder to delivery method mapping
FOLDER_TO_DELIVERY = {
    # PAID - Uses webhook to server 675908407617650697
    'uatb': {'method': 'webhook', 'url': PAID_SERVER_WEBHOOK},
    'diamond': {'method': 'webhook', 'url': PAID_SERVER_WEBHOOK},
    'paid_uatb': {'method': 'webhook', 'url': PAID_SERVER_WEBHOOK},
    'paid_diamond': {'method': 'webhook', 'url': PAID_SERVER_WEBHOOK},

    # FREE - Uses bot to server 1390050801136701642
    'free_cappers': {'method': 'bot', 'server': '1390050801136701642', 'channel': FREE_SERVER_CHANNELS['free_cappers']},
    'cappers_leaked': {'method': 'bot', 'server': '1390050801136701642', 'channel': FREE_SERVER_CHANNELS['cappers_leaked']},
    'exclusive_cappers': {'method': 'bot', 'server': '1390050801136701642', 'channel': FREE_SERVER_CHANNELS['exclusive_cappers']},
}

class DiscordForwarder:
    def __init__(self):
        self.stats = {
            'sent': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': datetime.now()
        }
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories"""
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directories ensured")

    def send_to_discord(self, webhook_url, message_data):
        """Send message to Discord via webhook"""
        if not webhook_url:
            return False, "No webhook configured"

        try:
            # Format the message
            channel = message_data.get('channel', 'Unknown')
            text = message_data.get('text', '[no text]')
            timestamp = message_data.get('timestamp', '')

            # Create Discord message
            discord_data = {
                'username': f'📡 {channel}',
                'content': text[:2000],  # Discord limit
                'embeds': [{
                    'footer': {
                        'text': f'{channel} • {timestamp[:19]}'
                    },
                    'color': 0x00ff00
                }]
            }

            # Send to Discord
            response = requests.post(webhook_url, json=discord_data)

            if response.status_code == 204:
                return True, "Sent"
            else:
                return False, f"HTTP {response.status_code}"

        except Exception as e:
            return False, str(e)

    def process_queue_folder(self, folder_name, delivery_config):
        """Process all messages in a queue folder"""
        folder_path = MESSAGE_QUEUE_DIR / folder_name

        if not folder_path.exists():
            return 0

        json_files = list(folder_path.glob("*.json"))

        if not json_files:
            return 0

        sent_count = 0
        print(f"\n📂 Processing {folder_name}: {len(json_files)} messages")

        for file_path in json_files:
            try:
                # Read message
                with open(file_path, 'r', encoding='utf-8') as f:
                    message_data = json.load(f)

                # Skip if no delivery config
                if not delivery_config:
                    print(f"  ⚠️  No delivery config for {folder_name}, skipping {file_path.name}")
                    self.stats['skipped'] += 1
                    continue

                # Send via appropriate method
                if delivery_config['method'] == 'webhook':
                    success, status = self.send_to_discord(delivery_config['url'], message_data)
                elif delivery_config['method'] == 'bot':
                    # TODO: Implement bot sending when bot is ready
                    print(f"  ⚠️  Bot delivery not yet implemented for {file_path.name}")
                    self.stats['skipped'] += 1
                    continue
                else:
                    print(f"  ❌ Unknown delivery method: {delivery_config['method']}")
                    self.stats['failed'] += 1
                    continue

                if success:
                    # Move to processed folder
                    processed_folder = PROCESSED_DIR / folder_name
                    processed_folder.mkdir(parents=True, exist_ok=True)

                    dest_path = processed_folder / file_path.name
                    file_path.rename(dest_path)

                    print(f"  ✅ Sent: {file_path.name}")
                    self.stats['sent'] += 1
                    sent_count += 1

                    # Rate limit
                    time.sleep(0.5)
                else:
                    print(f"  ❌ Failed: {file_path.name} - {status}")
                    self.stats['failed'] += 1

            except Exception as e:
                print(f"  ❌ Error with {file_path.name}: {e}")
                self.stats['failed'] += 1

        return sent_count

    def run_once(self):
        """Process all queue folders once"""
        print("\n🚀 DISCORD FORWARDER - PROCESSING QUEUES")
        print("=" * 50)
        print(f"Paid Server (675908407617650697): UATB, Diamond")
        print(f"Free Server (1390050801136701642): Free/Leaked")
        print("=" * 50)

        total_sent = 0

        # Process each folder
        for folder_name, delivery_config in FOLDER_TO_DELIVERY.items():
            sent = self.process_queue_folder(folder_name, delivery_config)
            total_sent += sent

        return total_sent

    def run_continuous(self):
        """Run continuous forwarding loop"""
        print("\n🚀 DISCORD FORWARDER STARTED")
        print("=" * 50)
        print(f"Queue Directory: {MESSAGE_QUEUE_DIR}")
        print(f"Paid Server Webhook: {'✅' if PAID_SERVER_WEBHOOK else '❌'}")
        print(f"Free Server Channels: {'✅' if FREE_SERVER_CHANNELS else '❌'}")
        print(f"Delivery Methods: {len(FOLDER_TO_DELIVERY)} configured")
        print("=" * 50)

        while True:
            try:
                sent = self.run_once()

                if sent > 0:
                    print(f"\n📊 Batch complete: {sent} messages sent")
                    self.print_stats()

                time.sleep(10)  # Check every 10 seconds

            except KeyboardInterrupt:
                print("\n👋 Stopping forwarder...")
                self.print_final_stats()
                break
            except Exception as e:
                print(f"\n❌ Error in main loop: {e}")
                time.sleep(30)

    def print_stats(self):
        """Print current statistics"""
        runtime = datetime.now() - self.stats['start_time']
        print(f"📊 Stats - Runtime: {runtime}, Sent: {self.stats['sent']}, "
              f"Failed: {self.stats['failed']}, Skipped: {self.stats['skipped']}")

    def print_final_stats(self):
        """Print final statistics"""
        runtime = datetime.now() - self.stats['start_time']
        print("\n" + "=" * 50)
        print("FINAL STATISTICS")
        print("=" * 50)
        print(f"Runtime: {runtime}")
        print(f"Messages sent: {self.stats['sent']}")
        print(f"Messages failed: {self.stats['failed']}")
        print(f"Messages skipped: {self.stats['skipped']}")
        print("=" * 50)

def main():
    forwarder = DiscordForwarder()

    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run once and exit
        sent = forwarder.run_once()
        print(f"\n✅ One-time forwarding complete: {sent} messages sent")
        forwarder.print_stats()
    else:
        # Run continuously
        forwarder.run_continuous()

if __name__ == '__main__':
    main()