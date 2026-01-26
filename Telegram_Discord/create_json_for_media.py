#!/usr/bin/env python
"""
Create JSON metadata files for existing media files in inbox
This allows the router to process them
"""
import os
import json
from pathlib import Path
from datetime import datetime
import re

# Configuration
INBOX_DIR = Path("C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord\\inbox")

# Default chat mapping based on filename patterns
# You can adjust these based on your file naming
CHANNEL_PATTERNS = {
    "uatb": -1002177758646,
    "diamond": -1002470080886,
    "cappers": -1002592669126,
    "leaked": -1001560546587,
    "exclusive": -1002608783933,
}

def guess_chat_id(filename):
    """Try to guess chat ID from filename"""
    filename_lower = filename.lower()

    # Try to extract chat ID from filename if it exists
    # Format: 20250925_211000_12476.jpg might have chat info
    if "_" in filename:
        parts = filename.split("_")
        # Check if there's a number that might be a chat ID
        for part in parts:
            try:
                num = int(part)
                # Telegram chat IDs are usually large negative numbers
                if num > 1000000000 or num < -1000000000:
                    return num
            except:
                pass

    # Otherwise, default to UATB channel for now
    # You can change this default
    return -1002177758646  # Default to UATB

def create_json_for_media(media_file):
    """Create JSON metadata for a media file"""
    media_path = INBOX_DIR / media_file

    # Skip if already has corresponding JSON
    json_file = media_path.with_suffix('.json')
    if json_file.exists():
        print(f"JSON already exists for {media_file}")
        return False

    # Extract info from filename
    # Format: 20250925_211000_12476.jpg
    basename = media_path.stem
    parts = basename.split('_')

    try:
        date_str = parts[0] if len(parts) > 0 else datetime.now().strftime('%Y%m%d')
        time_str = parts[1] if len(parts) > 1 else datetime.now().strftime('%H%M%S')
        msg_id = parts[2] if len(parts) > 2 else "0"
    except:
        date_str = datetime.now().strftime('%Y%m%d')
        time_str = datetime.now().strftime('%H%M%S')
        msg_id = "0"

    # Create timestamp
    try:
        dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
    except:
        dt = datetime.now()

    # Guess chat ID
    chat_id = guess_chat_id(media_file)

    # Determine media type
    ext = media_path.suffix.lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
        media_type = 'photo'
    elif ext in ['.mp4', '.mov', '.avi']:
        media_type = 'video'
    else:
        media_type = 'document'

    # Create payload
    payload = {
        "id": int(msg_id) if msg_id.isdigit() else 0,
        "chat_id": chat_id,
        "chat_title": "Recovered Media",
        "sender_id": 0,
        "type": media_type,
        "text": f"[Recovered media from {basename}]",
        "media_path": str(media_file),
        "ts_iso": dt.isoformat() + "Z",
        "has_media": True,
        "recovered": True,  # Mark as recovered
        "raw": {}
    }

    # Save JSON
    json_path = INBOX_DIR / f"{basename}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Created JSON for {media_file} -> {json_path.name}")
    return True

def main():
    """Process all media files in inbox"""
    if not INBOX_DIR.exists():
        print(f"Inbox directory not found: {INBOX_DIR}")
        return

    # Find all media files
    media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.webp']
    media_files = []

    for ext in media_extensions:
        media_files.extend(INBOX_DIR.glob(f"*{ext}"))

    print(f"Found {len(media_files)} media files in inbox")

    if not media_files:
        print("No media files to process")
        return

    # Create JSON for each
    created = 0
    for media_file in media_files:
        if create_json_for_media(media_file.name):
            created += 1

    print(f"\nCreated {created} new JSON files")
    print("The router should now be able to process these messages")

if __name__ == "__main__":
    main()