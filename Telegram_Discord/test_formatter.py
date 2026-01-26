#!/usr/bin/env python3
import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.utils.picks_formatter import format_clean_picks

# Test with your exact sample
test_text = """CAPPERS FREE💥
PardonMyPick
KBO MAXPLAY STree 3u
SSG LANDERS ML -110
PC KBO 2u
LG TWINS ML 2 21:48 +105"""

print("Testing formatter with sample data:")
print("="*50)
print("INPUT:")
print(test_text)
print("="*50)
print("OUTPUT:")
result = format_clean_picks("Test Channel", test_text, "")
print(result)
print("="*50)

# Test another common format
test_text2 = """CAPPERS FREE
Cblez
NBA 🏀
Lakers ML -150 2u MAX
Warriors +5.5 -110 1u"""

print("\nTest 2:")
print("INPUT:")
print(test_text2)
print("="*50)
print("OUTPUT:")
result2 = format_clean_picks("Premium Channel", test_text2, "")
print(result2)