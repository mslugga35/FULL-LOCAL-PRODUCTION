#!/usr/bin/env python3
"""
Create test PAID messages for UATB and Diamond channels
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Paths
MESSAGE_QUEUE_DIR = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\message_queue")

# Create test messages
test_messages = [
    {
        "channel": "UATB",
        "chat_id": -1002177758646,
        "folder": "paid_uatb",
        "messages": [
            "🏀 NBA PREMIUM PICK: Lakers -3.5 vs Warriors",
            "⚾ MLB LOCK: Yankees ML vs Red Sox",
            "🏈 NFL SUNDAY: Chiefs -7 vs Raiders"
        ]
    },
    {
        "channel": "DIAMOND 💎 VIP",
        "chat_id": -1002470080886,
        "folder": "paid_diamond",
        "messages": [
            "💎 DIAMOND VIP: Dodgers -1.5 Run Line",
            "💎 PREMIUM: Over 47.5 Total Points",
            "💎 EXCLUSIVE: Celtics -5.5 vs Heat"
        ]
    }
]

def create_test_messages():
    """Create test paid messages"""
    total_created = 0
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for channel_info in test_messages:
        channel = channel_info["channel"]
        chat_id = channel_info["chat_id"]
        folder = channel_info["folder"]

        # Create folder
        folder_path = MESSAGE_QUEUE_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Creating messages for {channel} in {folder}...")

        for i, text in enumerate(channel_info["messages"]):
            message_data = {
                "channel": channel,
                "chat_id": chat_id,
                "text": text,
                "timestamp": timestamp,
                "message_id": 5000 + total_created,
                "type": "paid"
            }

            # Create filename
            filename = f"test_paid_{folder}_{i+1}.json"
            filepath = folder_path / filename

            # Write message
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)

            print(f"  ✅ Created: {filename}")
            total_created += 1

    print(f"\n✅ Created {total_created} test PAID messages")
    print("\nFolders:")
    print("  📁 message_queue/paid_uatb - 3 messages")
    print("  📁 message_queue/paid_diamond - 3 messages")

    return total_created

if __name__ == '__main__':
    print("CREATING TEST PAID MESSAGES")
    print("=" * 50)
    create_test_messages()
    print("\nNow run: python send_paid_messages.py")