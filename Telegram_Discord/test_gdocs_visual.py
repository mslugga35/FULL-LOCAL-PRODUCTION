#!/usr/bin/env python3
"""
Visual Testing System for Google Docs Export
Uses Playwright to screenshot the actual Google Doc so you can see what gets exported
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from export_to_gdocs import PicksAggregator, GoogleDocsExporter

load_dotenv()

GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")
OUTPUT_DIR = Path(__file__).parent / "test_screenshots"
OUTPUT_DIR.mkdir(exist_ok=True)

def export_and_screenshot():
    """Export picks to Google Docs and take screenshot"""

    print("=" * 60)
    print("STEP 1: Loading picks from sent_archive...")
    print("=" * 60)

    # Load and display picks
    aggregator = PicksAggregator()
    total_picks, channels = aggregator.load_picks()

    print(f"\n✅ Loaded {total_picks} picks from {channels} channel(s)\n")

    # Show what will be exported
    print("=" * 60)
    print("STEP 2: Preview of export content...")
    print("=" * 60)
    content = aggregator.format_for_google_docs()
    print(content)
    print()

    # Export to Google Docs
    print("=" * 60)
    print("STEP 3: Exporting to Google Docs...")
    print("=" * 60)
    exporter = GoogleDocsExporter()
    success = exporter.update_document(content)

    if not success:
        print("❌ Export failed!")
        return False

    print(f"✅ Export successful!")
    print(f"📄 Document: https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit\n")

    # Take screenshot with Playwright
    print("=" * 60)
    print("STEP 4: Taking screenshot of Google Doc...")
    print("=" * 60)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to False to see browser
        page = browser.new_page(viewport={'width': 1280, 'height': 1024})

        # Navigate to Google Doc (view-only public link)
        doc_url = f"https://docs.google.com/document/d/{GOOGLE_DOC_ID}/preview"
        print(f"Opening: {doc_url}")
        page.goto(doc_url, wait_until="networkidle", timeout=30000)

        # Wait for content to load
        page.wait_for_timeout(3000)

        # Take full page screenshot
        screenshot_path = OUTPUT_DIR / f"gdocs_export_{Path(__file__).stem}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)

        print(f"✅ Screenshot saved: {screenshot_path}")

        browser.close()

    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print(f"📸 Screenshot: {screenshot_path}")
    print(f"📄 Google Doc: https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit")

    return True

if __name__ == "__main__":
    try:
        export_and_screenshot()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
