#!/usr/bin/env python3
import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.utils.picks_formatter import format_clean_picks

# Test with SeekingReturns example
test1 = """SeekingReturns
@srcgroup 5m ago
NYM CHC Over 7 (DK) -120 5u
NYM CHC F5 Over 3.5 (DK) -130 3u
NYM CHC F7 Over 5.5 (DK) -115 3u"""

print("Test 1 - SeekingReturns:")
print("=" * 50)
result1 = format_clean_picks("Premium Channel", test1, "")
print(result1)
print()

# Test with CAPPERS FREE and @cappersfree
test2 = """CAPPERS FREE💥
PorterPicks
@everyone
persfree CLEVELAND GUARDIANS (-1.5) () over Detroit +145
@fast persfree
@wi
@pl"""

print("Test 2 - PorterPicks with noise:")
print("=" * 50)
result2 = format_clean_picks("Test Channel", test2, "")
print(result2)
print()

# Test with multiple CAPPERS FREE
test3 = """CAPPERS FREE💥
McBets
Guardians ML () -140 1.5u
CAPPERS FREE💥
ppers
ersfree Sfree CINCINNATI REDS () over Pittsburgh Pirates -113"""

print("Test 3 - Multiple CAPPERS FREE:")
print("=" * 50)
result3 = format_clean_picks("Test Channel", test3, "")
print(result3)
print()

# Test with Discord bot artifacts
test4 = """Data Extractor Bot
APP
 — Yesterday at 4:30 PM
CAPPERS FREE💥
codycoverspreads
MLB 09/24
Orioles ML
Phillies ML
Yankees -1.5"""

print("Test 4 - Discord bot artifacts:")
print("=" * 50)
result4 = format_clean_picks("Test Channel", test4, "")
print(result4)
print()

# Test with @cappers mentions
test5 = """CAPPERS FREE💥
SmartMoneySports
@P
Detroit Tigers (, 6:30e) +134 2u
@cappers"""

print("Test 5 - @cappers mentions:")
print("=" * 50)
result5 = format_clean_picks("Test Channel", test5, "")
print(result5)
print()

# Test complex multi-pick format
test6 = """CAPPERS FREE💥
A11Bets
Padres ML () -135 0.75u
Guardians ML () -145 0.75u
Reds ML () -120 0.75u
Cubs ML () -120 0.75u"""

print("Test 6 - A11Bets multi-picks:")
print("=" * 50)
result6 = format_clean_picks("Test Channel", test6, "")
print(result6)