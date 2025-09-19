#!/usr/bin/env python3
"""
PRODUCTION SESSION AUTHENTICATION
- Non-blocking authentication with timeout
- Proper session string export
- No hanging on connection issues
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeRequiredError

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
API_ID = 29479443
API_HASH = "e3a7a7226cf446bbfd5366f7da75cdfa"
CONNECTION_TIMEOUT = 30
BASE_DIR = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION")

# Target channels for verification
TARGET_CHANNELS = {
    -1002177758646: "UATB",
    -1002470080886: "Diamond/Chamba",
    -1002592669126: "Cappers Free",
    -1001560546587: "Cappers Leaked",
    -1002608783933: "Exclusive Cappers"
}

def setup_logging():
    """Setup logging for auth process"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(BASE_DIR / 'auth.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

async def authenticate_with_timeout():
    """Authenticate with connection timeout"""
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("TELEGRAM SESSION AUTHENTICATION")
    logger.info("=" * 60)

    # Check for existing session string
    env_session = os.getenv("TELEGRAM_STRING_SESSION")
    if env_session and len(env_session) > 100:
        logger.info("Existing session string found, testing...")
        if await test_existing_session(env_session):
            logger.info("✓ Existing session is valid!")
            return env_session
        else:
            logger.warning("Existing session invalid, creating new one...")

    try:
        # Create client with string session
        client = TelegramClient(StringSession(), API_ID, API_HASH)

        logger.info("Connecting to Telegram...")

        # Connect with timeout
        connect_task = asyncio.create_task(client.connect())
        try:
            await asyncio.wait_for(connect_task, timeout=CONNECTION_TIMEOUT)
        except asyncio.TimeoutError:
            logger.error("❌ Connection timeout - check internet connection")
            return None

        # Check if already authorized
        if await client.is_user_authorized():
            logger.info("✓ Already authorized!")
            session_string = StringSession.save(client.session)
            await client.disconnect()
            return session_string

        # Get phone number
        logger.info("Authentication required...")
        phone = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()

        if not phone.startswith('+'):
            phone = '+' + phone

        # Send code with timeout
        logger.info("Sending verification code...")
        code_task = asyncio.create_task(client.send_code_request(phone))
        try:
            await asyncio.wait_for(code_task, timeout=CONNECTION_TIMEOUT)
        except asyncio.TimeoutError:
            logger.error("❌ Code request timeout")
            await client.disconnect()
            return None

        # Get verification code
        code = input("Enter the verification code you received: ").strip()

        try:
            # Sign in with timeout
            signin_task = asyncio.create_task(client.sign_in(phone, code))
            await asyncio.wait_for(signin_task, timeout=CONNECTION_TIMEOUT)

        except SessionPasswordNeededError:
            # Two-factor authentication
            logger.info("Two-factor authentication required")
            password = input("Enter your 2FA password: ").strip()

            password_task = asyncio.create_task(client.sign_in(password=password))
            await asyncio.wait_for(password_task, timeout=CONNECTION_TIMEOUT)

        except asyncio.TimeoutError:
            logger.error("❌ Sign-in timeout")
            await client.disconnect()
            return None

        # Verify successful authentication
        if not await client.is_user_authorized():
            logger.error("❌ Authentication failed")
            await client.disconnect()
            return None

        # Get user info
        me = await client.get_me()
        logger.info(f"✓ Authenticated as: {me.first_name} (@{me.username})")

        # Test channel access
        logger.info("Testing channel access...")
        accessible_count = 0

        for channel_id, name in TARGET_CHANNELS.items():
            try:
                entity = await asyncio.wait_for(
                    client.get_entity(channel_id),
                    timeout=10
                )
                logger.info(f"  ✓ {name} - Accessible")
                accessible_count += 1
            except Exception as e:
                logger.warning(f"  ✗ {name} - {str(e)[:50]}")

        if accessible_count == 0:
            logger.error("❌ No target channels accessible!")
            await client.disconnect()
            return None

        logger.info(f"✓ Access verified for {accessible_count}/{len(TARGET_CHANNELS)} channels")

        # Get session string
        session_string = StringSession.save(client.session)
        await client.disconnect()

        # Save to environment file
        env_file = BASE_DIR / '.env'
        logger.info(f"Saving session to {env_file}")

        # Read existing .env
        env_content = ""
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.read()

        # Update or add session string
        lines = env_content.split('\n')
        session_line = f"TELEGRAM_STRING_SESSION={session_string}"

        # Replace existing or add new
        session_found = False
        for i, line in enumerate(lines):
            if line.startswith('TELEGRAM_STRING_SESSION='):
                lines[i] = session_line
                session_found = True
                break

        if not session_found:
            lines.append(session_line)

        # Write back to file
        with open(env_file, 'w') as f:
            f.write('\n'.join(lines))

        logger.info("✓ Session saved successfully!")
        logger.info("=" * 60)
        logger.info("AUTHENTICATION COMPLETE")
        logger.info("You can now run the collector:")
        logger.info("python telegram_production_collector.py")
        logger.info("=" * 60)

        return session_string

    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        if 'client' in locals():
            await client.disconnect()
        return None

async def test_existing_session(session_string: str) -> bool:
    """Test if existing session is valid"""
    logger = logging.getLogger(__name__)

    try:
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)

        # Connect with timeout
        connect_task = asyncio.create_task(client.connect())
        await asyncio.wait_for(connect_task, timeout=CONNECTION_TIMEOUT)

        # Check authorization
        if not await client.is_user_authorized():
            await client.disconnect()
            return False

        # Test basic functionality
        me = await client.get_me()
        logger.info(f"Session valid for: {me.first_name} (@{me.username})")

        await client.disconnect()
        return True

    except Exception as e:
        logger.debug(f"Session test failed: {e}")
        if 'client' in locals():
            try:
                await client.disconnect()
            except:
                pass
        return False

def main():
    """Main function"""
    try:
        # Ensure base directory exists
        BASE_DIR.mkdir(exist_ok=True)

        # Run authentication
        session_string = asyncio.run(authenticate_with_timeout())

        if session_string:
            print("\n" + "="*60)
            print("✓ SUCCESS! Authentication complete.")
            print("Session saved and ready for production use.")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("❌ FAILED! Authentication unsuccessful.")
            print("Please check your internet connection and try again.")
            print("="*60)
            return 1

    except KeyboardInterrupt:
        print("\n❌ Authentication cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())