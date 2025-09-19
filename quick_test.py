#!/usr/bin/env python3
"""
Quick test - use existing session file
"""
import asyncio
import sys
import os
from telethon import TelegramClient

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Use same session path as working script
SESSION_PATH = r"C:\Users\mpmmo\discord-forwarder-bot\PRODUCTION\anon.session"
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

async def main():
    print("QUICK TEST STARTING...")

    # Check if session exists
    if not os.path.exists(SESSION_PATH):
        print(f"ERROR: Session file not found: {SESSION_PATH}")
        return

    print(f"Using session: {SESSION_PATH}")

    client = TelegramClient(SESSION_PATH, api_id, api_hash)

    try:
        await client.start()
        print("Connected!")

        me = await client.get_me()
        print(f"User: {me.first_name}")

        # Quick message test
        await client.send_message("+3212629156", "QUICK TEST MESSAGE - System is working!")
        print("Message sent!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())