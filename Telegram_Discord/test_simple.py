#!/usr/bin/env python3
"""Simple test of formatter with real data patterns"""

import sys
sys.path.append('src')

from utils.picks_formatter import format_clean_picks

# Test cases from real data
test_cases = [
    {
        "label": "Test 1 - Travy promo",
        "text": "Travy\n➖➖➖➖➖\nDM➡️@cappersfree✅",
        "ocr": ""
    },
    {
        "label": "Test 2 - vegasmirabet alias",
        "text": "vegasmirabet\n➖➖➖➖➖\nDM➡️@cappersfree✅",
        "ocr": ""
    },
    {
        "label": "Test 3 - OutofLineBets",
        "text": "OutofLineBets\n➖➖➖➖➖\nDM➡️@cappersfree✅",
        "ocr": ""
    },
    {
        "label": "Test 4 - With fake picks",
        "text": "Travy\nNBA: Warriors ML +150 2u\nMLB: Yankees -1.5 -110 1.5u",
        "ocr": ""
    },
    {
        "label": "Test 5 - CAPPERS FREE spam",
        "text": "CAPPERS FREE 💥\n@YourDailyCapper ✅✅ DM➡️ for VIP\nMLB: Brewers -1.5 (+110) 2u\nNBA: Warriors ML -145 1.5u",
        "ocr": ""
    }
]

print("Testing new formatter with real data patterns...")
print("=" * 60)

for test in test_cases:
    print(f"\n{test['label']}")
    print(f"Input: {test['text']}")
    
    result = format_clean_picks("free_cappers", test['text'], test['ocr'])
    
    # Convert result to safe ASCII for display
    safe_result = result.encode('ascii', 'ignore').decode('ascii')
    print(f"Output: {safe_result}")
    print("-" * 40)
