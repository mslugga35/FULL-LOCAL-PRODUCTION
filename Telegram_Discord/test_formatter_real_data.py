#!/usr/bin/env python3
"""Test the new formatter with real yesterday's data"""

import json
import glob
import sys
import os
sys.path.append('src')

from utils.picks_formatter import format_clean_picks

def test_real_data():
    # Get some real files from yesterday
    pattern = "sent_archive/20250918/free_cappers/*.json"
    files = glob.glob(pattern)[:10]  # test first 10
    
    print(f"Testing {len(files)} real files from yesterday...")
    print("=" * 60)
    
    for i, filepath in enumerate(files):
        print(f"\n--- File {i+1}: {os.path.basename(filepath)} ---")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract data
            text = data.get('text', '')
            chat_title = data.get('chat_title', 'unknown')
            
            # Look for OCR data (might be in a separate file or embedded)
            ocr_text = data.get('ocr_text', '')
            
            # Safe print for unicode
            print(f"Original text: {text.encode('ascii', 'ignore').decode('ascii')}")
            if ocr_text:
                print(f"OCR text: {ocr_text.encode('ascii', 'ignore').decode('ascii')}")
            
            # Test new formatter
            result = format_clean_picks(chat_title, text, ocr_text)
            print(f"Formatted output:")
            print(result)
            print("-" * 40)
            
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    test_real_data()