#!/usr/bin/env python3
import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.utils.picks_formatter import format_clean_picks

# Test with the exact problematic message
test_message = """CAPPERS FREE💥
BetSharper
MLB Pirates +1.5
Twins ML
Dodgeppersfree -15
NFL
Cardinals +1.5 (POD)"""

print("Testing current problematic message:")
print("=" * 50)
print("INPUT:")
print(test_message)
print("=" * 50)
print("OUTPUT:")
result = format_clean_picks("Test Channel", test_message, "")
print(result)
print("=" * 50)