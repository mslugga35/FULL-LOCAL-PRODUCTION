#!/usr/bin/env python
"""
Add a test channel to the Telegram collector configuration
"""
import os
import sys

print("=" * 60)
print("ADD TEST CHANNEL TO TELEGRAM COLLECTOR")
print("=" * 60)
print()
print("To get your test channel ID:")
print("1. Open Telegram Web: https://web.telegram.org")
print("2. Go to your test channel")
print("3. Look at the URL - it will show something like:")
print("   https://web.telegram.org/k/#-1234567890")
print("4. Copy the number (including the minus sign)")
print()
print("Common ID formats:")
print("  Private group: -1001234567890")
print("  Public channel: -1001234567890")
print("  Supergroup: -1001234567890")
print()
print("-" * 60)

# Get channel info from user
channel_id = input("Enter your test channel ID (with minus sign): ").strip()
channel_name = input("Enter a name for this channel (e.g., 'My Test'): ").strip()

if not channel_id.startswith("-"):
    print("Warning: Channel ID should start with a minus sign")
    channel_id = "-" + channel_id

try:
    channel_id = int(channel_id)
except ValueError:
    print("Error: Invalid channel ID format")
    sys.exit(1)

# Create the queue name (where messages will be routed)
queue_name = "test_channel"

print()
print("Configuration to add:")
print("-" * 40)
print(f"Channel ID: {channel_id}")
print(f"Channel Name: {channel_name}")
print(f"Queue Name: {queue_name}")
print()

confirm = input("Add this channel to configuration? (y/n): ").lower()

if confirm == 'y':
    # Update the routing map
    config_file = "config/channel_routing_map.py"

    with open(config_file, 'r') as f:
        content = f.read()

    # Find the ROUTING_MAP section
    import_end = content.find("ROUTING_MAP = {")
    map_end = content.find("}", import_end)

    # Add the new channel
    new_line = f'    {channel_id}: "{queue_name}",      # {channel_name}\n'

    # Insert before the closing brace
    new_content = content[:map_end] + new_line + content[map_end:]

    # Backup the original file
    import shutil
    shutil.copy(config_file, config_file + ".backup")

    # Write the updated configuration
    with open(config_file, 'w') as f:
        f.write(new_content)

    print("✅ Channel added to configuration!")
    print()
    print("Next steps:")
    print("1. Check if Discord target exists in discord_targets.yaml")
    print("2. Restart the Telegram collector: pm2 restart tg-collector")
    print("3. Send a test message in your channel")
    print("4. Check the inbox folder for new messages")

    # Also create the queue folder
    queue_path = f"message_queue/{queue_name}"
    os.makedirs(queue_path, exist_ok=True)
    print(f"\n✅ Created queue folder: {queue_path}")

else:
    print("Cancelled - no changes made")