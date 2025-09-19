#!/usr/bin/env python3
import os
import asyncio
from telethon import TelegramClient

# Configuration
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"
phone = "+3212629156"
session_file = "C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\telegram_session"

async def main():
    print("==============================================")
    print("TELEGRAM AUTHENTICATION SETUP")
    print("==============================================")
    print(f"Phone: {phone}")
    print(f"Session: {session_file}")
    print("==============================================")

    client = TelegramClient(session_file, api_id, api_hash)

    await client.start(phone=phone)

    print("\n[SUCCESS] Authentication successful!")
    print("Session saved to:", session_file + ".session")

    # Test by getting user info
    me = await client.get_me()
    print(f"\nLogged in as: {me.username or me.first_name}")
    print(f"User ID: {me.id}")

    await client.disconnect()
    print("\n[SUCCESS] Setup complete! You can now run the telegram collector.")

if __name__ == "__main__":
    asyncio.run(main())