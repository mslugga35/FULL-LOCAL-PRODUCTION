#!/usr/bin/env python3
"""
Simple test script for the updated picks formatter using sample text
"""
import os
import sys

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.picks_formatter import format_clean_picks

def test_sample(name, sample_text):
    """Test a sample text with our formatter"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)
    
    print("INPUT TEXT:")
    print("-" * 40)
    # Handle unicode safely
    try:
        print(sample_text)
    except UnicodeEncodeError:
        print(sample_text.encode('ascii', 'replace').decode('ascii'))
    print()
    
    # Apply our formatter
    formatted = format_clean_picks("test_channel", "", sample_text)
    
    print("FORMATTED OUTPUT:")
    print("-" * 40)
    try:
        print(formatted)
    except UnicodeEncodeError:
        print(formatted.encode('ascii', 'replace').decode('ascii'))
    print()

def main():
    """Test the formatter on sample texts based on what we saw in images"""
    
    # Sample 1: @cappersfree with Dolphins pick (simplified)
    sample1 = """09/18/2025
@cappersfree
Play Of The Day
Dolphins +11.5
Matchup: MIA @ Buffalo
Kickoff: 7:15 p.m. CT

Top Opinion Plays
Dolphins ML
Matchup: MIA @ Buffalo"""

    # Sample 2: NFL Bills pick 
    sample2 = """NFL:
9 point 2 pick teaser:
Bills -2 / over 41.5
5%"""

    # Sample 3: Marlins ML with @cappersfree
    sample3 = """Wednesday Whale Plays
@cappersfree
Marlins ML (MLB)

Straight Bet: 1 Unit
1 Unit = 10% Bankroll"""

    # Sample 4: Classic CAPPERS FREE spam
    sample4 = """CAPPERS FREE
DM for VIP packages
@YourDailyCapper
Lakers ML -145 (2u)
Warriors +4.5 (+110) 1u MAX
Subscribe for premium picks"""

    # Sample 5: Known capper with aliases
    sample5 = """CBLEZ.
NBA tonight:
Lakers ML -145 2u
Warriors +7.5 1.5u
Celtics over 220.5 1u"""

    # Sample 6: VegasMira variant
    sample6 = """vegas mira bet
NFL Sunday:
Cowboys -3.5 +110
Patriots ML +125 
2u each"""

    # Sample 7: No play message
    sample7 = """@cappersfree
Nothing I like tonight, off day
Back tomorrow with fire picks
DM for VIP packages"""

    # Sample 8: YourDailyCapper test
    sample8 = """yourdailycapper
MLB today:
Twins ML 1u
Athletics ML 1u
Royals +1.5 2u"""

    test_samples = [
        ("Dolphins @cappersfree pick", sample1),
        ("NFL Bills teaser", sample2), 
        ("Marlins ML @cappersfree", sample3),
        ("CAPPERS FREE spam", sample4),
        ("CBLEZ alias test", sample5),
        ("VegasMira alias test", sample6),
        ("No play message", sample7),
        ("YourDailyCapper test", sample8),
    ]
    
    for name, sample in test_samples:
        test_sample(name, sample)
    
    print(f"\n{'='*60}")
    print("Testing complete!")
    print('='*60)

if __name__ == "__main__":
    main()