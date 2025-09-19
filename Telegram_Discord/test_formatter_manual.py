#!/usr/bin/env python3
"""
Manual test of the picks formatter with sample text
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.picks_formatter import format_clean_picks

# Test samples based on what we saw in the images
test_samples = [
    {
        "name": "Whale Play with @cappersfree",
        "text": """Wednesday Whale Plays
@cappersfree
Marlins ML (MLB)

Straight Bet: 1 Unit
1 Unit = 10% Bankroll"""
    },
    {
        "name": "Play of the Day with promo",
        "text": """09/18/2025

@cappersfree
Play Of The Day

• 🔒 Dolphins +11.5 🔒

Matchup: MIA @ Buffalo

Kickoff: 7:15 p.m. CT (that's 8:15 p.m. ET)


Top Opinion Plays

• 🔥 Dolphins ML 🔥

Matchup: MIA @ Buffalo

Kickoff: 7:15 p.m. CT (that's 8:15 p.m. ET)"""
    },
    {
        "name": "CAPPERS FREE spam",
        "text": """CAPPERS FREE 💥
DM➡️✅ for VIP packages
@YourDailyCapper
MLB: Brewers -1.5 (+110) 2u
NBA: Warriors ML -145 1.5u MAX"""
    },
    {
        "name": "Cblez variant test",
        "text": """CBLEZ.
Yankees ML -120
2 units"""
    },
    {
        "name": "No play message",
        "text": """@cappersfree
Nothing I like tonight boys
Back tomorrow with some heat"""
    },
    {
        "name": "PlatinumLocks test",
        "text": """PlatinumLocks
Bears +3.5 (-110) 
Over 44.5 (-105)
3u each"""
    }
]

def main():
    print("TESTING PICKS FORMATTER")
    print("=" * 50)
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\nTEST {i}: {sample['name']}")
        print("-" * 40)
        print("INPUT:")
        try:
            print(sample['text'])
        except UnicodeEncodeError:
            print("[text with emojis - see raw below]")
        print("\nFORMATTED OUTPUT:")
        result = format_clean_picks("test_label", "", sample['text'])
        print(result)
        print("-" * 40)

if __name__ == "__main__":
    main()