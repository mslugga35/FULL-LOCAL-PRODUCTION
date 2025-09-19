#!/usr/bin/env python3
"""
Test script to analyze formatter performance on yesterday's free_cappers messages
"""
import json
import os
import sys
from pathlib import Path

# Add src to path to import our formatter
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils.picks_formatter import format_clean_picks

def load_yesterday_messages():
    """Load all messages from yesterday's sent_archive/free_cappers"""
    archive_path = Path(__file__).parent.parent / "sent_archive" / "20250918" / "free_cappers"
    messages = []
    
    if not archive_path.exists():
        print(f"Archive path not found: {archive_path}")
        return messages
    
    for json_file in archive_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                messages.append({
                    'file': json_file.name,
                    'data': data
                })
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    print(f"Loaded {len(messages)} messages from yesterday")
    return messages

def test_formatter_on_messages(messages, limit=20):
    """Test formatter on sample messages and show results"""
    print("\n" + "="*80)
    print("FORMATTER TEST RESULTS")
    print("="*80)
    
    results = []
    
    for i, msg in enumerate(messages[:limit]):
        print(f"\n--- MESSAGE {i+1}: {msg['file']} ---")
        
        data = msg['data']
        text = data.get('text', '')
        ocr_text = data.get('ocr_text', '')
        
        # Show original content
        print("\nORIGINAL TEXT:")
        if text:
            print(f"  Text: {text[:200]}{'...' if len(text) > 200 else ''}")
        if ocr_text:
            print(f"  OCR: {ocr_text[:200]}{'...' if len(ocr_text) > 200 else ''}")
        
        # Test formatter
        try:
            formatted = format_clean_picks("free_cappers", text, ocr_text)
            print("\nFORMATTED OUTPUT:")
            print(formatted)
            
            results.append({
                'file': msg['file'],
                'success': True,
                'formatted': formatted,
                'original_text': text,
                'original_ocr': ocr_text
            })
        except Exception as e:
            print(f"\nFORMATTER ERROR: {e}")
            results.append({
                'file': msg['file'],
                'success': False,
                'error': str(e),
                'original_text': text,
                'original_ocr': ocr_text
            })
        
        print("-" * 60)
    
    return results

def analyze_results(results):
    """Analyze and summarize the test results"""
    print(f"\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    print(f"Total messages tested: {total}")
    print(f"Successfully formatted: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed to format: {failed} ({failed/total*100:.1f}%)")
    
    # Show errors if any
    if failed > 0:
        print(f"\nERRORS:")
        for r in results:
            if not r['success']:
                print(f"  {r['file']}: {r['error']}")
    
    # Show capper detection stats
    print(f"\nCAPPER DETECTION:")
    cappers_found = {}
    no_capper_count = 0
    
    for r in results:
        if r['success']:
            lines = r['formatted'].split('\n')
            capper_line = None
            for line in lines:
                if line.startswith('**') and not line.startswith('**free_cappers**'):
                    capper_line = line.strip('*')
                    break
            
            if capper_line:
                cappers_found[capper_line] = cappers_found.get(capper_line, 0) + 1
            else:
                no_capper_count += 1
    
    print(f"  Messages with identified cappers: {len(cappers_found)}")
    print(f"  Messages without capper: {no_capper_count}")
    
    if cappers_found:
        print(f"\n  Top cappers found:")
        for capper, count in sorted(cappers_found.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {capper}: {count} messages")

def main():
    """Main test function"""
    print("Loading yesterday's free_cappers messages...")
    messages = load_yesterday_messages()
    
    if not messages:
        print("No messages found to test!")
        return
    
    # Test on sample of messages
    print(f"\nTesting formatter on first 20 messages...")
    results = test_formatter_on_messages(messages, limit=20)
    
    # Analyze results
    analyze_results(results)
    
    # Save results for further analysis
    output_file = Path(__file__).parent / "test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()