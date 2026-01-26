#!/usr/bin/env python3
"""
Testing System for Google Docs Export
Compares what's in Telegram vs what will be exported to Google Docs
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from export_to_gdocs import PicksAggregator, FREE_CHANNELS

load_dotenv()

TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/New_York"))
SENT_ARCHIVE_DIR = Path(__file__).parent / "sent_archive"
today = datetime.now(TIMEZONE).strftime("%Y%m%d")

def main():
    print("=" * 80)
    print(" GOOGLE DOCS EXPORT TEST - COMPARISON TOOL")
    print("=" * 80)
    print()

    # Step 1: Show what's in Telegram (raw JSON files)
    print("STEP 1: RAW TELEGRAM DATA (from sent_archive)")
    print("-" * 80)

    for channel_key, channel_config in FREE_CHANNELS.items():
        folder_name = channel_config["folder"]
        channel_path = SENT_ARCHIVE_DIR / today / folder_name

        if not channel_path.exists():
            print(f"\n{channel_config['name']}: No data for today")
            continue

        json_files = sorted(list(channel_path.glob("*.json")))
        # Strip emojis from channel name for console display
        name_ascii = ''.join(c for c in channel_config['name'] if ord(c) < 128) or folder_name
        print(f"\n{name_ascii}: {len(json_files)} messages")
        print()

        for idx, json_file in enumerate(json_files, 1):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Get timestamp
            raw_date = data.get('raw', {}).get('date', '')
            if raw_date:
                pick_time = datetime.fromisoformat(str(raw_date))
                pick_time = pick_time.astimezone(TIMEZONE)
                time_str = pick_time.strftime("%I:%M %p")
            else:
                time_str = "??:??"

            # Get text
            text = data.get('text', '').strip()
            if not text:
                text = "[IMAGE ONLY]"

            # Strip emojis for console display
            text_ascii = ''.join(c for c in text if ord(c) < 128)
            if not text_ascii.strip():
                text_ascii = "[Contains emojis/special chars]"

            # Show raw data
            print(f"  {idx}. [{time_str}] {text_ascii[:100]}")
            if data.get('has_media'):
                media_path = data.get('media_path', '')
                print(f"      [Media]: {Path(media_path).name if media_path else 'Unknown'}")

    print()
    print("=" * 80)
    print()

    # Step 2: Show what will be exported
    print("STEP 2: EXPORTED OUTPUT (after filtering)")
    print("-" * 80)

    aggregator = PicksAggregator()
    total_picks, channels = aggregator.load_picks()

    if total_picks == 0:
        print("\n[Warning] NO PICKS TO EXPORT")
    else:
        content = aggregator.format_for_google_docs()
        print()
        # Save to file instead of printing (avoid emoji encoding issues)
        with open('test_output_formatted.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        print("[Output saved to test_output_formatted.txt]")
        print(f"Lines: {len(content.splitlines())}")
        print(f"Characters: {len(content)}")

    print()
    print("=" * 80)
    print()

    # Step 3: Summary comparison
    print("STEP 3: FILTERING SUMMARY")
    print("-" * 80)
    print()

    patterns_filtered = [
        "@cappersfree",
        "DM arrow",
        "divider lines",
        "Messages from AI",
        "VIP package",
        "cheapest prices",
        "join the best team"
    ]

    print("[Filter] The following patterns are being filtered out:")
    for pattern in patterns_filtered:
        print(f"   [X] {pattern}")

    print()
    print("[Keep] What WILL appear:")
    print("   - Capper names (VEGASMIRABET, VC, ISW, TRAVY, CHAMBA, etc.)")
    print("   - Actual pick content (OCR from images)")
    print("   - Timestamps (from actual Telegram message time)")
    print()

    print("=" * 80)
    print(f" RESULT: {total_picks} picks will be exported")
    print("=" * 80)

if __name__ == "__main__":
    main()
