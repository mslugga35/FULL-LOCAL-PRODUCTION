#!/usr/bin/env python3
"""
Test Discord bot access to paid channel
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
BASE_PATH = Path(__file__).parent
load_dotenv(BASE_PATH / ".env")

# Configuration
CHANNEL_ID = "1403837637730762875"  # Your paid channel
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN_FREE", "").strip()

if not BOT_TOKEN:
    print("ERROR: Missing DISCORD_BOT_TOKEN_FREE in .env")
    sys.exit(1)

print("Testing Discord Bot Access to Paid Channel")
print("=" * 50)
print(f"Channel ID: {CHANNEL_ID}")
print(f"Bot Token: {BOT_TOKEN[:20]}...")

# Test sending a message
url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
headers = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json"
}

test_message = {
    "content": "🔧 **TEST MESSAGE**\nVerifying bot access to paid channel.\nIf you see this, the bot has permissions! ✅"
}

print("\nAttempting to send test message...")
response = requests.post(url, headers=headers, json=test_message)

if response.status_code == 200:
    print("SUCCESS! Bot can send to paid channel.")
    print("Message sent successfully!")
elif response.status_code == 403:
    print("PERMISSION DENIED!")
    print("The bot doesn't have permission to send to this channel.")
    print("Please check:")
    print("1. The bot is in the server")
    print("2. The bot has 'Send Messages' permission in this channel")
elif response.status_code == 404:
    print("CHANNEL NOT FOUND!")
    print("Either the channel doesn't exist or the bot can't see it.")
else:
    print(f"ERROR: {response.status_code}")
    print(f"Response: {response.text[:200]}")

print("\n" + "=" * 50)