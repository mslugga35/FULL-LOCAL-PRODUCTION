#!/usr/bin/env python3
import sys
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SESSION_STRING = "1AQAOMTQ5LjE1NC4xNzUuNTcBu2g+yaG4eWVh5epPtcgWfQTPkqasIdvsxCj68U7clUx9mn3LsVTRIXr/0xJoWABsu/2Khznce7EyhPh0wMw4aFTKllNmUA+iJsGib4sQfpd5dMcg0Ua3BR9JCx596L7qNzAhSda7R2grZFv5cnyx5oT39iXIA3edgHUpf0n+0XwfFFwK8oIqoJgPvoThCpwPit2iCXGM1LERLzssLErvGYzUeAklhKBvle3OJJRFPz4GQIkSRiVQLutLHHXUh3uLws7Pauq/fuhTbd8KxQ5987wcrXlwGI7iUOskQkc+vGlDuXUr3pgbsRHZ5qnIycCnWE3GhO/ns5OtXvJ8PbvkMjQ="
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

async def main():
    print("SENDING TODAY VALIDATION...")

    client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)
    await client.start()

    message = f"""TELEGRAM SYSTEM STATUS

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Universal Capture: RUNNING
Production Collector: RUNNING
Today Message Puller: RUNNING

Ready to capture ANY message from ANY channel
- Text messages
- Photos/Videos
- Documents (PDF, Word, etc)
- Audio/Voice notes
- Stickers

All files saved to inbox folder
System is LIVE and monitoring!"""

    try:
        await client.send_message("+3212629156", message)
        print("MESSAGE SENT TO +3212629156")
    except Exception as e:
        print(f"SEND FAILED: {e}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())