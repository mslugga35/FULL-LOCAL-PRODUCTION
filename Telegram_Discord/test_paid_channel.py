#!/usr/bin/env python3
"""Test sending a message to the paid Discord channel"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment
BASE_PATH = Path(__file__).parent
load_dotenv(BASE_PATH / ".env")

# Get bot token
bot_token = os.getenv("DISCORD_BOT_TOKEN_FREE", "").strip()
if not bot_token:
    print("ERROR: Missing DISCORD_BOT_TOKEN_FREE")
    exit(1)

# Channel ID for paid messages
channel_id = "1403837637730762875"

# Test message
test_message = "🔧 **Test Message**\nThis is a test to verify the bot can send to the paid channel.\n\nIf you see this, the bot has access!"

# Send via Discord API
url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
headers = {
    "Authorization": f"Bot {bot_token}",
    "Content-Type": "application/json"
}
data = {
    "content": test_message
}

print(f"Testing send to channel {channel_id}...")
response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print("✅ SUCCESS! Message sent to paid channel!")
    print("Check your Discord channel to confirm.")
elif response.status_code == 403:
    print("❌ FORBIDDEN: Bot lacks permission to send to this channel")
    print("Please ensure the bot has 'Send Messages' permission in this channel")
elif response.status_code == 404:
    print("❌ NOT FOUND: Channel doesn't exist or bot can't see it")
    print("Please ensure the bot is in the server and can view the channel")
else:
    print(f"❌ ERROR {response.status_code}: {response.text}")