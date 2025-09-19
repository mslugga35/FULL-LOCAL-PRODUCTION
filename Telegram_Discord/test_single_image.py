#!/usr/bin/env python3
"""
Test a single image through OCR and formatter - simpler version
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.picks_formatter import format_clean_picks

# Simulate OCR text from the images we saw
test_ocr_1 = """Wednesday Whale Plays
@cappersfree
Marlins ML (MLB)

Straight Bet: 1 Unit
1 Unit = 10% Bankroll"""

test_ocr_2 = """09/18/2025

@cappersfree
Play Of The Day

Dolphins +11.5

Matchup: MIA @ Buffalo

Kickoff: 7:15 p.m. CT (that's 8:15 p.m. ET)


Top Opinion Plays

Dolphins ML

Matchup: MIA @ Buffalo

Kickoff: 7:15 p.m. CT (that's 8:15 p.m. ET)"""

print("=== TEST 1: Whale Play ===")
result1 = format_clean_picks("free_cappers", "", test_ocr_1)
print(result1)

print("\n=== TEST 2: Play of the Day ===")
result2 = format_clean_picks("free_cappers", "", test_ocr_2)
print(result2)

# Test with a known capper in the text
test_ocr_3 = """@cappersfree
YourDailyCapper
MLB: Yankees ML -150 2u
NBA: Lakers +5.5 (-110) 1u"""

print("\n=== TEST 3: YourDailyCapper ===")
result3 = format_clean_picks("free_cappers", "", test_ocr_3)
print(result3)