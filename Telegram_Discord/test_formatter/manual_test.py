#!/usr/bin/env python3
"""
Manual test script with sample betting content to test formatter
"""
import sys
from pathlib import Path

# Add src to path to import our formatter
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils.picks_formatter import format_clean_picks

def test_formatter_samples():
    """Test formatter with various sample inputs"""
    
    test_cases = [
        {
            "name": "CAPPERS FREE with DuckInvestments picks",
            "text": "",
            "ocr_text": """CAPPERS FREE
@DuckInvestments DM for VIP
MLB: Brewers -1.5 (+110) 2u
NBA: Warriors ML -145 1.5u
NFL: Chiefs -3.5 (-110) 1u MAX"""
        },
        {
            "name": "Travy Friday Premium",
            "text": "Travy",
            "ocr_text": """Travy
Friday Premium Plays
Braves ML (1U)
Padres -1.5
White Sox ML
Parlay: Padres ML + Braves ML"""
        },
        {
            "name": "YourDailyCapper with units",
            "text": "",
            "ocr_text": """YourDailyCapper
Twins ML (1U)
Kansas St ML (1U)
Athletics ML (1U)"""
        },
        {
            "name": "CBLEZ with noise",
            "text": "cblez.",
            "ocr_text": """CAPPERS FREE / DM for promo walls
Cblez
Lakers ML +120 2u
Over 215.5 (-110) 1.5u
------"""
        },
        {
            "name": "No play message",
            "text": "vegasmira",
            "ocr_text": """vegas mira bet
No bet tonight - off day
Nothing I like today
Back tomorrow with picks"""
        },
        {
            "name": "Alias test - nickycashin",
            "text": "",
            "ocr_text": """nickycashin
Cowboys -7 (-110) 2u
49ers ML +180 1u"""
        },
        {
            "name": "Just promo spam",
            "text": "",
            "ocr_text": """CAPPERS FREE
DM @cappersfree
Join VIP for premium picks
Best prices guaranteed"""
        }
    ]
    
    print("FORMATTER TEST RESULTS")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- TEST {i}: {test['name']} ---")
        
        print("\nINPUT:")
        if test['text']:
            print(f"  Text: {test['text']}")
        if test['ocr_text']:
            print(f"  OCR: {test['ocr_text']}")
        
        try:
            formatted = format_clean_picks("free_cappers", test['text'], test['ocr_text'])
            print("\nFORMATTED OUTPUT:")
            print(formatted)
            
        except Exception as e:
            print(f"\nERROR: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_formatter_samples()