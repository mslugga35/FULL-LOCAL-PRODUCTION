#!/usr/bin/env python3
"""
TELEGRAM RE-AUTHENTICATION SCRIPT
Run this to create a new working session
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# API credentials
API_ID = 29479443
API_HASH = "e3a7a7226cf446bbfd5366f7da75cdfa"

async def main():
    print("=" * 50)
    print("TELEGRAM AUTHENTICATION")
    print("=" * 50)
    print("\nThis will create a new working session.")
    print("You'll need your phone number and the code Telegram sends.\n")

    # Create new session
    client = TelegramClient('NEW_telegram_session', API_ID, API_HASH)

    await client.start()

    # If we get here, authentication worked
    print("\n✅ SUCCESS! Authenticated to Telegram")

    # Get user info
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username})")

    # Test UATB access
    print("\nTesting UATB access...")
    try:
        uatb = await client.get_entity(-1002177758646)
        print(f"✅ Can access UATB: {uatb.title}")

        # Get latest message
        async for msg in client.iter_messages(uatb, limit=1):
            print(f"Latest message: {msg.date.strftime('%H:%M')} - {(msg.text[:50] if msg.text else '[Media]')}")

    except Exception as e:
        print(f"❌ Cannot access UATB: {e}")

    # Save session string
    session_string = StringSession.save(client.session)

    print("\n" + "=" * 50)
    print("NEW SESSION STRING (save this!):")
    print("=" * 50)
    print(session_string)
    print("=" * 50)

    # Save to file
    with open('NEW_SESSION_STRING.txt', 'w') as f:
        f.write(session_string)
    print("\n✅ Saved to NEW_SESSION_STRING.txt")

    await client.disconnect()
    print("\nDone! You can now use this session in your bots.")

if __name__ == "__main__":
    asyncio.run(main())