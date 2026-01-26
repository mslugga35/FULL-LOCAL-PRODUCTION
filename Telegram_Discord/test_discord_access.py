#!/usr/bin/env python3
"""Test Discord bot access to paid channel"""
import os
import asyncio
import discord
from dotenv import load_dotenv
from pathlib import Path

# Load environment
BASE_PATH = Path(__file__).parent
load_dotenv(BASE_PATH / ".env")

async def test_channel_access():
    """Test if bot can access the paid channel"""

    # Get bot token
    bot_token = os.getenv("DISCORD_BOT_TOKEN_FREE", "").strip()
    if not bot_token:
        print("ERROR: Missing DISCORD_BOT_TOKEN_FREE in .env")
        return

    # Discord client
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"✓ Logged in as {client.user}")

        # Test paid channel access
        paid_channel_id = 1403837637730762875

        try:
            channel = await client.fetch_channel(paid_channel_id)
            print(f"✓ Can access paid channel: #{channel.name}")

            # Try to send a test message
            try:
                await channel.send("🔧 Test message from bot - checking paid channel access")
                print("✓ Successfully sent test message to paid channel!")
            except discord.Forbidden:
                print("✗ Bot lacks permission to send messages in paid channel")
            except Exception as e:
                print(f"✗ Error sending message: {e}")

        except discord.Forbidden:
            print("✗ Bot cannot access paid channel (missing permissions)")
        except discord.NotFound:
            print("✗ Paid channel not found (wrong ID or bot not in server)")
        except Exception as e:
            print(f"✗ Error accessing channel: {e}")

        await client.close()

    try:
        await client.start(bot_token)
    except Exception as e:
        print(f"✗ Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(test_channel_access())