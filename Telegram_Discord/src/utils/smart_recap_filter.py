"""
Smart Recap Filter - Uses AI to distinguish picks from recaps

A PICK looks like:
- "Florida -8 2U" (team, spread, units)
- "Duquesne -2.5 (-110) v. Rhode Island 6u"
- Shows: team, spread/ML, odds, units

A RECAP looks like:
- "✅ Florida -8 WON" (has result indicator)
- "Yesterday we went 5-2"
- "Record: 45-30"
- Shows: checkmarks/X, Won/Lost, past tense, scores

Key insight: Recaps have OUTCOMES, picks have PREDICTIONS
"""

import re
from datetime import datetime, timedelta

def is_recap_smart(text: str, ocr_text: str = "") -> bool:
    """
    Smart recap detection - returns True only if CONFIDENT it's a recap.
    
    Rules:
    1. Must have RESULT INDICATOR (✅/❌ or Won/Lost)
    2. AND must have OUTCOME LANGUAGE (past tense, final score)
    3. NOT just having a date or "record" mention
    """
    full_text = f"{text}\n{ocr_text}".lower()
    
    # === STRONG RECAP INDICATORS (need multiple) ===
    
    # Result emojis
    has_checkmark = bool(re.search(r'[\u2705\u2611\u2714]', full_text))  # ✅ ☑ ✔
    has_x_mark = bool(re.search(r'[\u274C\u274E]', full_text))  # ❌ ❎
    has_result_emoji = has_checkmark or has_x_mark
    
    # Result words (must be standalone, not part of "to win")
    has_won_lost = bool(re.search(r'\b(won|lost|winner|loser|cashed|busted|hit|miss)\b', full_text))
    
    # Past tense language
    has_past_language = bool(re.search(r'\b(yesterday|last night|went \d+-\d+|finished|ended)\b', full_text))
    
    # Final scores (like "94-102" or "Lakers 94 - Heat 102")
    has_final_score = bool(re.search(r'\b\d{2,3}\s*[-–]\s*\d{2,3}\b', full_text))
    
    # Explicit recap words
    has_recap_word = bool(re.search(r'\b(recap|results?|review)\b', full_text))
    
    # === PICK INDICATORS (these suggest it's NOT a recap) ===
    
    # Unit sizing (1U, 2U, 5u, etc.) - picks have this
    has_units = bool(re.search(r'\b\d+\.?\d*\s*u\b', full_text))
    
    # Future dates (today, tomorrow, tonight)
    has_future = bool(re.search(r'\b(today|tonight|tomorrow|this (afternoon|evening))\b', full_text))
    
    # Active bet language
    has_active = bool(re.search(r'\b(lock|play|pick|bet|taking|riding)\b', full_text))
    
    # "Cash out available" = active bet, not result
    has_cash_out = bool(re.search(r'cash\s*out\s*(available)?', full_text))
    
    # === DECISION LOGIC ===
    
    # Strong pick indicators override recap suspicion
    if has_cash_out:
        return False  # Active bet slip, not recap
    
    if has_future and has_units:
        return False  # Looks like today's pick with units
    
    # Need MULTIPLE strong recap indicators
    recap_score = 0
    if has_result_emoji:
        recap_score += 2  # Strong indicator
    if has_won_lost:
        recap_score += 2  # Strong indicator
    if has_past_language:
        recap_score += 2  # Strong indicator
    if has_final_score:
        recap_score += 1  # Medium indicator (could be projected scores)
    if has_recap_word:
        recap_score += 3  # Very strong indicator
    
    # Pick indicators reduce recap score
    if has_units:
        recap_score -= 2  # Picks have units
    if has_active:
        recap_score -= 1  # Active language
    
    # Only filter if recap score is HIGH (3+)
    return recap_score >= 3


def is_todays_game(text: str, ocr_text: str = "") -> bool:
    """
    Check if the pick appears to be for today's or tomorrow's games.
    Returns True if it seems current, False if it looks like old data.
    """
    full_text = f"{text}\n{ocr_text}"
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    
    # Check for explicit dates
    today_patterns = [
        today.strftime("%m/%d"),      # 02/01
        f"{today.month}/{today.day}",  # 2/1
        today.strftime("%m-%d"),      # 02-01
        f"{today.strftime('%B')} {today.day}",  # February 1
        f"{today.strftime('%b')} {today.day}",  # Feb 1
    ]
    
    tomorrow_patterns = [
        tomorrow.strftime("%m/%d"),
        f"{tomorrow.month}/{tomorrow.day}",
        tomorrow.strftime("%m-%d"),
    ]
    
    yesterday_patterns = [
        yesterday.strftime("%m/%d"),
        f"{yesterday.month}/{yesterday.day}",
        yesterday.strftime("%m-%d"),
    ]
    
    # If has today's or tomorrow's date, it's current
    for pattern in today_patterns + tomorrow_patterns:
        if pattern in full_text:
            return True
    
    # If has yesterday's date, likely a recap
    for pattern in yesterday_patterns:
        if pattern in full_text:
            return False
    
    # If has "today" or "tonight" or "tomorrow", it's current
    if re.search(r'\b(today|tonight|tomorrow)\b', full_text, re.I):
        return True
    
    # If has "yesterday", it's old
    if re.search(r'\byesterday\b', full_text, re.I):
        return False
    
    # Default: assume current (don't filter if unsure)
    return True


def should_filter_message(text: str, ocr_text: str = "") -> tuple[bool, str]:
    """
    Main filter function. Returns (should_filter, reason).
    
    Only filters if CONFIDENT it's a recap.
    When in doubt, let it through.
    """
    # Check if it's a recap
    if is_recap_smart(text, ocr_text):
        return True, "recap_detected"
    
    # Check if it's for old games
    if not is_todays_game(text, ocr_text):
        return True, "old_game"
    
    # Let it through
    return False, "ok"


# Test cases
if __name__ == "__main__":
    test_cases = [
        # Should PASS (today's picks)
        ("Florida -8 2U", "", "pick"),
        ("Duquesne -2.5 (-110) v. Rhode Island 6u", "", "pick"),
        ("2/1/26 Early Card: NCAAB", "", "pick"),
        ("Full Card 02/02", "", "pick"),  # Tomorrow
        ("Cash Out available", "", "pick"),  # Active bet
        
        # Should FILTER (recaps)
        ("✅ Florida -8 WON", "", "recap"),
        ("Yesterday we went 5-2", "", "recap"),
        ("❌ Lakers +3 Lost", "", "recap"),
        ("Record: 45-30 this month", "", "recap"),
        ("Recap: Great day yesterday!", "", "recap"),
    ]
    
    print("Testing smart recap filter:\n")
    for text, ocr, expected in test_cases:
        should_filter, reason = should_filter_message(text, ocr)
        result = "FILTER" if should_filter else "PASS"
        status = "✅" if (result == "FILTER" and expected == "recap") or (result == "PASS" and expected == "pick") else "❌"
        print(f"{status} '{text[:40]}...' -> {result} ({reason}) [expected: {expected}]")
