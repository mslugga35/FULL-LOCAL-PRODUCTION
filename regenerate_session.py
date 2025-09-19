#!/usr/bin/env python3
"""
Regenerate Telegram session with proper timeout handling
This script will create a fresh session if the current one is corrupted
"""
import os
import sys
import asyncio
import time
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"
phone = "+3212629156"

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}", flush=True)

async def test_existing_session():
    """Test if existing session still works"""
    existing_session = "1AQAOMTQ5LjE1NC4xNzUuNTcBu2g+yaG4eWVh5epPtcgWfQTPkqasIdvsxCj68U7clUx9mn3LsVTRIXr/0xJoWABsu/2Khznce7EyhPh0wMw4aFTKllNmUA+iJsGib4sQfpd5dMcg0Ua3BR9JCx596L7qNzAhSda7R2grZFv5cnyx5oT39iXIA3edgHUpf0n+0XwfFFwK8oIqoJgPvoThCpwPit2iCXGM1LERLzssLErvGYzUeAklhKBvle3OJJRFPz4GQIkSRiVQLutLHHXUh3uLws7Pauq/fuhTbd8KxQ5987wcrXlwGI7iUOskQkc+vGlDuXUr3pgbsRHZ5qnIycCnWE3GhO/ns5OtXvJ8PbvkMjQ="

    try:
        log("Testing existing StringSession...")
        client = TelegramClient(StringSession(existing_session), api_id, api_hash)

        log("Attempting connection (15s timeout)...")
        await asyncio.wait_for(client.connect(), timeout=15.0)

        if await client.is_user_authorized():
            me = await client.get_me()
            log(f"✓ Existing session works! User: {me.first_name}")
            await client.disconnect()
            return True
        else:
            log("✗ Existing session not authorized")
            await client.disconnect()
            return False

    except asyncio.TimeoutError:
        log("✗ Existing session timed out")
        return False
    except Exception as e:
        log(f"✗ Existing session error: {e}")
        return False

async def create_new_session():
    """Create a new session interactively"""
    log("Creating new Telegram session...")

    # Remove any existing session files that might interfere
    session_files = [f for f in os.listdir('.') if f.endswith('.session')]
    for sf in session_files:
        try:
            os.rename(sf, f"{sf}.backup")
            log(f"Backed up: {sf}")
        except:
            pass

    client = TelegramClient('new_session', api_id, api_hash)

    try:
        log("Connecting...")
        await client.connect()

        if not await client.is_user_authorized():
            log(f"Sending code to {phone}...")
            await client.send_code_request(phone)

            code = input("Enter the code you received: ")
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Two-factor authentication enabled. Enter your password: ")
                await client.sign_in(password=password)

        # Get user info
        me = await client.get_me()
        log(f"✓ Logged in as: {me.first_name} {me.last_name or ''}")

        # Export string session
        string_session = client.session.save()
        log("✓ Session created successfully!")

        # Save to file
        with open('new_session_string.txt', 'w') as f:
            f.write(string_session)

        log("=" * 60)
        log("NEW SESSION STRING:")
        log(string_session)
        log("=" * 60)
        log("Session saved to: new_session_string.txt")

        await client.disconnect()
        return string_session

    except Exception as e:
        log(f"Error creating session: {e}")
        await client.disconnect()
        return None

async def main():
    log("=== TELEGRAM SESSION REGENERATION ===")

    # First test existing session
    if await test_existing_session():
        log("Existing session is working fine - no need to regenerate")
        return

    log("Existing session failed - creating new one...")
    new_session = await create_new_session()

    if new_session:
        log("✓ New session created successfully!")
        log("Update your scripts with the new session string")
    else:
        log("✗ Failed to create new session")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Interrupted by user")
    except Exception as e:
        log(f"Fatal error: {e}")