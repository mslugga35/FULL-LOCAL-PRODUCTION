#!/usr/bin/env python3
"""
Focused test for specific formatter issues
"""
import os
import sys

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.picks_formatter import format_clean_picks

def test_sample(name, sample_text, expected_capper=None):
    """Test a sample text with our formatter"""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print('='*50)
    
    # Apply our formatter
    formatted = format_clean_picks("test", "", sample_text)
    
    print("FORMATTED OUTPUT:")
    print("-" * 30)
    try:
        print(formatted)
    except UnicodeEncodeError:
        print(formatted.encode('ascii', 'replace').decode('ascii'))
    
    if expected_capper:
        if f"**{expected_capper}**" in formatted:
            print(f"[OK] Correctly detected capper: {expected_capper}")
        else:
            print(f"[FAIL] Expected capper: {expected_capper}")
    print()

def main():
    """Test specific patterns"""
    
    # Test 1: YourDailyCapper should be detected
    test_sample("YourDailyCapper basic", "YourDailyCapper\nTwins ML 1u", "YourDailyCapper")
    
    # Test 2: CBLEZ alias should map to Cblez
    test_sample("CBLEZ alias", "CBLEZ\nLakers ML -145", "Cblez")
    
    # Test 3: vegas mira bet should map to vegasmirabet
    test_sample("VegasMira alias", "vegas mira bet\nCowboys -3.5", "vegasmirabet")
    
    # Test 4: @cappersfree should be filtered out, no capper detected
    test_sample("@cappersfree filter", "@cappersfree\nDolphins +11.5", None)
    
    # Test 5: No play message should be detected
    test_sample("No play detection", "Nothing I like tonight, off day", None)
    
    # Test 6: Multiple picks should be extracted properly
    test_sample("Multiple picks", "Travy\nBraves ML 1u\nPadres -1.5\nWhite Sox ML", "Travy")

if __name__ == "__main__":
    main()