#!/usr/bin/env python3
"""Catch up on messages from the last 3 hours"""
import os
import sys
import json
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv()

# Configuration
INBOX = r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\inbox"
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

# Channels to monitor (from channel_routing_map.py)
CHANNELS = {
    -1002177758646: "UATB",
    -1002470080886: "Diamond",
    -1002592669126: "Cap