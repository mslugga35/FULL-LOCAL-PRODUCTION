#!/usr/bin/env python3
"""
Simple test script for formatter - handles unicode better
"""
import json
import os
import sys
from pathlib import Path

# Add src to path to import our formatter
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils.picks_formatter import format_clean_picks

def safe_print(text, max_len=150):
    """Safely print text with unicode handling"""
    try:
        # Replace problematic chars and limit length
        clean_text = text.encode('ascii', 'replace').decode('ascii')
        if len(clean_text) > max_len:
            clean_text = clean_text[:max_len] + "..."
        print(clean_text)
    except:
        print("[unprintable content]")

def test_recent_messages():
    """Test formatter on a few recent messages"""
    archive_path = Path(__file__).parent.parent / "sent_archive" / "20250918" / "free_cappers"
    
    if not archive_path.exists():
        print(f"Archive path not found: {archive_path}")
        return
    
    # Get first 5 message files
    json_files = list(archive_path.glob("*.json"))[:5]
    
    print(f"Testing formatter on {len(json_files)} messages...")
    print("=" * 60)
    
    for i, json_file in enumerate(json_files, 1):
        print(f"\nMESSAGE {i}: {json_file.name}")
        print("-" * 40)
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            text = data.get('text', '')
            ocr_text = data.get('ocr_text', '')
            
            print("ORIGINAL:")
            if text:
                print("  Text:", end=" ")
                safe_print(text)
            if ocr_text:
                print("  OCR:", end=" ")
                safe_print(ocr_text)
            
            # Test formatter
            formatted = format_clean_picks("free_cappers", text, ocr_text)
            
            print("\nFORMATTED:")
            safe_print(formatted, max_len=300)
            
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_recent_messages()