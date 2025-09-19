#!/usr/bin/env python3
"""
Find messages with OCR content to test formatter
"""
import json
import os
from pathlib import Path

def find_ocr_messages():
    """Find messages that have OCR text"""
    archive_path = Path(__file__).parent.parent / "sent_archive" / "20250918" / "free_cappers"
    
    if not archive_path.exists():
        print(f"Archive path not found: {archive_path}")
        return []
    
    ocr_messages = []
    
    for json_file in archive_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'ocr_text' in data and data['ocr_text']:
                ocr_messages.append({
                    'file': json_file.name,
                    'text': data.get('text', ''),
                    'ocr_text': data['ocr_text']
                })
                
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
    
    print(f"Found {len(ocr_messages)} messages with OCR text")
    return ocr_messages

def show_samples(messages, count=3):
    """Show sample OCR messages"""
    for i, msg in enumerate(messages[:count], 1):
        print(f"\n--- SAMPLE {i}: {msg['file']} ---")
        print(f"Text: {msg['text'][:100]}{'...' if len(msg['text']) > 100 else ''}")
        print(f"OCR: {msg['ocr_text'][:200]}{'...' if len(msg['ocr_text']) > 200 else ''}")

if __name__ == "__main__":
    messages = find_ocr_messages()
    if messages:
        show_samples(messages)
        
        # Save sample for testing
        sample_file = Path(__file__).parent / "ocr_samples.json"
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(messages[:10], f, indent=2, ensure_ascii=False)
        print(f"\nSaved {min(10, len(messages))} samples to {sample_file}")
    else:
        print("No messages with OCR text found")