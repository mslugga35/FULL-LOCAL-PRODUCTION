#!/usr/bin/env python3
"""
Generate a fresh Telegram session
Saves both as file and string for flexibility
"""
import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Your API credentials
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

async def main():
    print("=" * 60)
    print("GENERATE FRESH TELEGRAM SESSION")
    print("=" * 60)
    print()

    # Create client with new session
    client = TelegramClient('new_session', api_id, api_hash)

    await client.start()

    print("[SUCCESS] Logged in!")

    # Get user info
    me = await client.get_me()
    print(f"[USER] {me.first_name} (@{me.username})")
    print(f"[PHONE] {me.phone}")

    # Export as string session
    string_session = StringSession.save(client.session)

    # Save to file
    with open("telegram_string_session.txt", "w") as f:
        f.write(string_session)

    print()
    print("[SAVED] Session saved to: telegram_string_session.txt")
    print()
    print("=" * 60)
    print("STRING SESSION (save this!):")
    print("=" * 60)
    print(string_session)
    print("=" * 60)

    await client.disconnect()
    print()
    print("[DONE] You can now use this session in your scripts!")

if __name__ == "__main__":
    asyncio.run(main())