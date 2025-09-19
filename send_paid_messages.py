#!/usr/bin/env python3
"""
Send PAID messages (UATB, Diamond) to Discord webhook
"""

import os
import json
import time
import requests
from pathlib import Path

# Paths
MESSAGE_QUEUE_DIR = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\message_queue")

# PAID Discord Webhook
PAID_WEBHOOK = 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN'

# PAID folders only
PAID_FOLDERS = ['paid_uatb', 'paid_diamond', 'uatb', 'diamond']

def send_to_discord(webhook_url, message_data):
    """Send message to Discord via webhook"""
    try:
        # Extract message details
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
                'color': 0x00ff00 if 'UATB' in channel else 0x0099ff
            }]
        }

        # Send to Discord
        response = requests.post(webhook_url, json=discord_data)

        if response.status_code == 204:
            return True, "Sent"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"

    except Exception as e:
        return False, str(e)

def process_paid_messages():
    """Process and send all PAID messages"""
    total_sent = 0
    total_failed = 0

    print("🚀 SENDING PAID MESSAGES TO DISCORD")
    print("=" * 50)
    print(f"Webhook: {PAID_WEBHOOK[:50]}...")
    print(f"Folders: {', '.join(PAID_FOLDERS)}")
    print("=" * 50)

    for folder_name in PAID_FOLDERS:
        folder_path = MESSAGE_QUEUE_DIR / folder_name

        if not folder_path.exists():
            print(f"⚠️  Folder {folder_name} does not exist, skipping...")
            continue

        json_files = list(folder_path.glob("*.json"))

        if not json_files:
            print(f"📁 {folder_name}: No messages to send")
            continue

        print(f"\n📁 Processing {folder_name}: {len(json_files)} messages")

        for file_path in json_files:
            try:
                # Read message
                with open(file_path, 'r', encoding='utf-8') as f:
                    message_data = json.load(f)

                # Send to Discord
                success, status = send_to_discord(PAID_WEBHOOK, message_data)

                if success:
                    # Move to processed folder
                    processed_folder = MESSAGE_QUEUE_DIR.parent / "processed_messages" / folder_name
                    processed_folder.mkdir(parents=True, exist_ok=True)

                    dest_path = processed_folder / file_path.name
                    file_path.rename(dest_path)

                    print(f"  ✅ Sent: {file_path.name}")
                    total_sent += 1

                    # Rate limit
                    time.sleep(0.5)
                else:
                    print(f"  ❌ Failed: {file_path.name} - {status}")
                    total_failed += 1

            except Exception as e:
                print(f"  ❌ Error with {file_path.name}: {e}")
                total_failed += 1

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"✅ Messages sent: {total_sent}")
    print(f"❌ Messages failed: {total_failed}")
    print("=" * 50)

    return total_sent, total_failed

if __name__ == '__main__':
    # First, let's check if there are any paid messages
    print("Checking for PAID messages...")

    has_messages = False
    for folder in PAID_FOLDERS:
        folder_path = MESSAGE_QUEUE_DIR / folder
        if folder_path.exists() and list(folder_path.glob("*.json")):
            has_messages = True
            break

    if not has_messages:
        print("No PAID messages to send at this time.")
        print("\nTo collect new messages, run the Telegram collector.")
    else:
        sent, failed = process_paid_messages()