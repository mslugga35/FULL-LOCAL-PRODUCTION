#!/usr/bin/env python3
"""
Windows Message Processor - Routes messages from recent_messages to message_queue
Fixed for Windows paths and actual channel names
"""

import os
import json
import shutil
import time
import sys
from pathlib import Path
from datetime import datetime
import io

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Windows paths
RECENT_MESSAGES_DIR = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\recent_messages")
MESSAGE_QUEUE_DIR = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\message_queue")

# Channel name to folder mapping (based on your actual Telegram channels)
CHANNEL_MAPPINGS = {
    # PAID CHANNELS - Route to paid folders for webhook delivery
    'UATB': 'paid_uatb',  # → Paid server via webhook
    '🌐 UATB 🌐': 'paid_uatb',  # → Paid server via webhook
    'DIAMOND': 'paid_diamond',  # → Paid server via webhook
    'DIAMOND 💎 VIP PACKAGE': 'paid_diamond',  # → Paid server via webhook
    'Diamond/Chamba': 'paid_diamond',  # → Paid server via webhook

    # FREE CHANNELS - Each goes to its specific Discord channel
    'Cappers Free': 'free_cappers',  # → Free server channel 1403894557615325216
    'CAPPERS FREE💥': 'free_cappers',  # → Free server channel 1403894557615325216
    'CBlez Bets (FREE)': 'free_cappers',  # → Free server channel 1403894557615325216

    # LEAKED - Goes to cappers-leaked channel
    'Cappers Leaked': 'cappers_leaked',  # → Free server channel 1403894596186017962
    'HANDICAPPERS LEAKED🔥': 'cappers_leaked',  # → Free server channel 1403894596186017962

    # EXCLUSIVE - Goes to exclusive-cappers channel
    'Exclusive Cappers': 'exclusive_cappers',  # → Free server channel 1403894653660692500
    '***EXCLUSIVE PLAYS***': 'exclusive_cappers',  # → Free server channel 1403894653660692500

    # Additional channels from recent messages
    'Big Dog Intel🐾': 'free_cappers',
    'MLB INTEL LAB ⚾️': 'free_cappers',
    'BETTING INTEL 🔌': 'free_cappers',
    'SHARK CASHOUT': 'free_cappers',
    'DATSQ9 UPDATES🔒': 'free_cappers',
    '️✨Glitch Picks✨': 'free_cappers',
    '⚡⚡ BILL BENTERS SURE PICKS ⚡⚡': 'free_cappers',
    'Discount Depot 🥇': 'free_cappers',
    'Bordervouches': 'free_cappers',
    'Borderannounce': 'free_cappers',
    'Border': 'free_cappers',
    '@cappers.group.buy on IG': 'free_cappers',
    '👑Cappers_picks_for_cheap(Personal Bets)👑': 'free_cappers',
    'YLose Gunz': 'free_cappers',
    'YLose Coach Rick': 'free_cappers',
    'YLose Members Updates': 'free_cappers',
    'TheCappersForum': 'free_cappers',
    'TheHiddenBagGrp': 'free_cappers',
    'The NC Sharp 🔪': 'free_cappers',
    '🔥MONDAY PACKAGE🔥': 'free_cappers',
    'Telegram': 'free_cappers',
    '💰': 'free_cappers',

    # Partial matches (case-insensitive)
    'free': 'free_cappers',
    'leaked': 'cappers_leaked',
    'exclusive': 'exclusive_cappers',
    'uatb': 'paid_uatb',
    'diamond': 'paid_diamond',
    'chamba': 'paid_diamond',
    'vip': 'paid_diamond',
    'premium': 'paid_diamond',
    'intel': 'free_cappers',
    'betting': 'free_cappers',
    'cappers': 'free_cappers'
}

class MessageProcessor:
    def __init__(self):
        self.stats = {
            'processed': 0,
            'routed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        self.ensure_directories()

    def ensure_directories(self):
        """Create all queue directories"""
        queue_folders = [
            'paid_uatb',           # UATB → Paid Discord
            'paid_diamond',        # Diamond/Chamba → Paid Discord
            'free_cappers',        # Cappers Free → Free Discord
            'cappers_leaked',      # Cappers Leaked → Free Discord
            'exclusive_cappers'    # Exclusive Cappers → Free Discord
        ]

        for folder in queue_folders:
            queue_path = MESSAGE_QUEUE_DIR / folder
            queue_path.mkdir(parents=True, exist_ok=True)

        print(f"✅ Queue directories ensured: {queue_folders}")

    def determine_queue_folder(self, message_data):
        """Determine which queue folder a message should go to"""
        # Get channel name from message
        channel = message_data.get('channel', '').strip()

        if not channel:
            return None

        # Try exact match first
        if channel in CHANNEL_MAPPINGS:
            return CHANNEL_MAPPINGS[channel]

        # Try case-insensitive partial match
        channel_lower = channel.lower()
        for pattern, folder in CHANNEL_MAPPINGS.items():
            if pattern.lower() in channel_lower:
                return folder

        # Check message text for clues
        text = message_data.get('text', '').lower()
        if 'uatb' in text:
            return 'paid_uatb'
        elif 'diamond' in text or 'chamba' in text:
            return 'paid_diamond'
        elif 'free' in text:
            return 'free_cappers'
        elif 'leaked' in text:
            return 'cappers_leaked'  # ✅ FIXED: leaked goes to free leaked channel
        elif 'exclusive' in text:
            return 'exclusive_cappers'  # ✅ FIXED: exclusive goes to free exclusive channel
        elif 'premium' in text:
            return 'paid_diamond'  # ✅ FIXED: premium goes to paid channel

        return None

    def process_message_file(self, file_path):
        """Process a single message file"""
        try:
            # Read message data
            with open(file_path, 'r', encoding='utf-8') as f:
                message_data = json.load(f)

            # Determine destination folder
            queue_folder = self.determine_queue_folder(message_data)

            if not queue_folder:
                print(f"  ⚠️  Cannot route {file_path.name} - unknown channel: {message_data.get('channel', 'N/A')}")
                return False

            # Add routing metadata
            message_data['routed_from'] = 'recent_messages'
            message_data['routed_to'] = queue_folder
            message_data['routed_at'] = datetime.now().isoformat()

            # Copy to destination queue folder
            dest_path = MESSAGE_QUEUE_DIR / queue_folder / file_path.name

            with open(dest_path, 'w', encoding='utf-8') as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)

            # Remove from recent_messages
            file_path.unlink()

            print(f"  ✅ Routed to {queue_folder}: {file_path.name}")
            self.stats['routed'] += 1
            return True

        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")
            self.stats['errors'] += 1
            return False

    def process_batch(self):
        """Process a batch of messages"""
        if not RECENT_MESSAGES_DIR.exists():
            print("⚠️  recent_messages directory not found")
            return 0

        # Get all JSON files
        json_files = list(RECENT_MESSAGES_DIR.glob("*.json"))

        if not json_files:
            return 0

        print(f"\n📥 Processing {len(json_files)} messages...")

        processed_count = 0
        for file_path in json_files:
            if self.process_message_file(file_path):
                processed_count += 1
            self.stats['processed'] += 1

        return processed_count

    def run_continuous(self):
        """Run continuous processing loop"""
        print("🚀 WINDOWS MESSAGE PROCESSOR STARTED")
        print("=" * 50)
        print(f"Source: {RECENT_MESSAGES_DIR}")
        print(f"Destination: {MESSAGE_QUEUE_DIR}")
        print("=" * 50)

        while True:
            try:
                processed = self.process_batch()

                if processed > 0:
                    print(f"\n📊 Batch complete: {processed} messages routed")
                    self.print_stats()

                time.sleep(10)  # Check every 10 seconds

            except KeyboardInterrupt:
                print("\n👋 Stopping processor...")
                self.print_final_stats()
                break
            except Exception as e:
                print(f"\n❌ Error in main loop: {e}")
                time.sleep(30)  # Wait longer on error

    def print_stats(self):
        """Print current statistics"""
        runtime = datetime.now() - self.stats['start_time']
        success_rate = (self.stats['routed'] / self.stats['processed'] * 100) if self.stats['processed'] > 0 else 0

        print(f"📊 Stats - Runtime: {runtime}, Processed: {self.stats['processed']}, "
              f"Routed: {self.stats['routed']} ({success_rate:.1f}%), Errors: {self.stats['errors']}")

    def print_final_stats(self):
        """Print final statistics"""
        runtime = datetime.now() - self.stats['start_time']
        print("\n" + "=" * 50)
        print("FINAL STATISTICS")
        print("=" * 50)
        print(f"Runtime: {runtime}")
        print(f"Messages processed: {self.stats['processed']}")
        print(f"Messages routed: {self.stats['routed']}")
        print(f"Errors: {self.stats['errors']}")
        if self.stats['processed'] > 0:
            success_rate = self.stats['routed'] / self.stats['processed'] * 100
            print(f"Success rate: {success_rate:.1f}%")
        print("=" * 50)

def main():
    processor = MessageProcessor()

    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run once and exit
        processed = processor.process_batch()
        print(f"✅ One-time processing complete: {processed} messages routed")
        processor.print_stats()
    else:
        # Run continuously
        processor.run_continuous()

if __name__ == '__main__':
    main()