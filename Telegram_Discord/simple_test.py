#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.picks_formatter import format_clean_picks

# Simple test without emojis
test1 = """CAPPERS FREE
DM for VIP
@YourDailyCapper
MLB: Brewers -1.5 (+110) 2u
NBA: Warriors ML -145 1.5u MAX"""

test2 = """CBLEZ.
Yankees ML -120
2 units"""

test3 = """PlatinumLocks
Bears +3.5 (-110) 
Over 44.5 (-105)
3u each"""

test4 = """Nothing I like tonight boys
Back tomorrow"""

print("=== TEST 1: YourDailyCapper ===")
result1 = format_clean_picks("test", "", test1)
print(result1)

print("\n=== TEST 2: Cblez alias ===")
result2 = format_clean_picks("test", "", test2)
print(result2)

print("\n=== TEST 3: PlatinumLocks alias ===")
result3 = format_clean_picks("test", "", test3)
print(result3)

print("\n=== TEST 4: No play ===")
result4 = format_clean_picks("test", "", test4)
print(result4)