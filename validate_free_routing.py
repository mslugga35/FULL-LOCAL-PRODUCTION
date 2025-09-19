#!/usr/bin/env python3
"""
FREE ROUTING VALIDATION SCRIPT
Ensures FREE content never leaks to premium channels
Tests the routing logic with various message scenarios
"""

import sys
import json
from pathlib import Path

# Import the fixed message processor
sys.path.append(str(Path(__file__).parent))
from message_processor_windows import MessageProcessor

def test_routing_scenarios():
    """Test various message scenarios to ensure proper routing"""
    processor = MessageProcessor()

    # Test scenarios
    test_cases = [
        # FREE CONTENT - Must stay FREE
        {
            'channel': 'Cappers Free',
            'text': 'Free pick for today',
            'expected': 'free_cappers',
            'category': 'FREE'
        },
        {
            'channel': 'CAPPERS FREE💥',
            'text': 'Here is a free tip',
            'expected': 'free_cappers',
            'category': 'FREE'
        },
        {
            'channel': 'Cappers Leaked',
            'text': 'Leaked picks from premium channel',
            'expected': 'cappers_leaked',
            'category': 'FREE'
        },
        {
            'channel': 'HANDICAPPERS LEAKED🔥',
            'text': 'Some leaked content here',
            'expected': 'cappers_leaked',
            'category': 'FREE'
        },
        {
            'channel': 'Exclusive Cappers',
            'text': 'Exclusive free content',
            'expected': 'exclusive_cappers',
            'category': 'FREE'
        },
        {
            'channel': '***EXCLUSIVE PLAYS***',
            'text': 'Exclusive content for members',
            'expected': 'exclusive_cappers',
            'category': 'FREE'
        },

        # Text-based routing for FREE content
        {
            'channel': 'Unknown Channel',
            'text': 'This is leaked from premium',
            'expected': 'cappers_leaked',
            'category': 'FREE'
        },
        {
            'channel': 'Unknown Channel',
            'text': 'Exclusive content here',
            'expected': 'exclusive_cappers',
            'category': 'FREE'
        },
        {
            'channel': 'Unknown Channel',
            'text': 'Free content available',
            'expected': 'free_cappers',
            'category': 'FREE'
        },

        # PAID CONTENT - Should go to paid channels
        {
            'channel': 'UATB',
            'text': 'UATB premium pick',
            'expected': 'paid_uatb',
            'category': 'PAID'
        },
        {
            'channel': '🌐 UATB 🌐',
            'text': 'Premium UATB content',
            'expected': 'paid_uatb',
            'category': 'PAID'
        },
        {
            'channel': 'Diamond/Chamba',
            'text': 'Diamond VIP pick',
            'expected': 'paid_diamond',
            'category': 'PAID'
        },
        {
            'channel': 'DIAMOND 💎 VIP PACKAGE',
            'text': 'Premium diamond content',
            'expected': 'paid_diamond',
            'category': 'PAID'
        },

        # Text-based routing for PAID content
        {
            'channel': 'Unknown Channel',
            'text': 'This is premium content only',
            'expected': 'paid_diamond',
            'category': 'PAID'
        },
        {
            'channel': 'Unknown Channel',
            'text': 'UATB special pick',
            'expected': 'paid_uatb',
            'category': 'PAID'
        },
        {
            'channel': 'Unknown Channel',
            'text': 'Diamond chamba pick',
            'expected': 'paid_diamond',
            'category': 'PAID'
        }
    ]

    print("🔍 VALIDATING FREE ROUTING PROTECTION")
    print("=" * 60)

    results = {
        'total': len(test_cases),
        'passed': 0,
        'failed': 0,
        'free_protected': 0,
        'paid_correct': 0
    }

    for i, test_case in enumerate(test_cases, 1):
        message_data = {
            'channel': test_case['channel'],
            'text': test_case['text']
        }

        actual = processor.determine_queue_folder(message_data)
        expected = test_case['expected']
        category = test_case['category']

        # Check result
        if actual == expected:
            status = "✅ PASS"
            results['passed'] += 1

            if category == 'FREE':
                results['free_protected'] += 1
            else:
                results['paid_correct'] += 1
        else:
            status = "❌ FAIL"
            results['failed'] += 1

        print(f"{i:2d}. [{category:4s}] {test_case['channel'][:25]:25s} → "
              f"Expected: {expected:15s} | Actual: {actual or 'None':15s} | {status}")

    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} {'❌' if results['failed'] > 0 else '✅'}")
    print(f"Free content protected: {results['free_protected']} ✅")
    print(f"Paid content correct: {results['paid_correct']} ✅")

    success_rate = (results['passed'] / results['total']) * 100
    print(f"Success rate: {success_rate:.1f}%")

    if results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED - FREE ROUTING PROTECTED! 🎉")
    else:
        print(f"\n⚠️  {results['failed']} TESTS FAILED - NEEDS ATTENTION")

    return results['failed'] == 0

def validate_delivery_config():
    """Validate that FREE folders don't use premium delivery methods"""
    print("\n🔍 VALIDATING DELIVERY CONFIGURATION")
    print("=" * 60)

    # Import the delivery config
    sys.path.append(str(Path(__file__).parent))
    from discord_forwarder_simple import FOLDER_TO_DELIVERY, FREE_SERVER_CHANNELS

    free_folders = ['free_cappers', 'cappers_leaked', 'exclusive_cappers']
    paid_folders = ['paid_uatb', 'paid_diamond']

    free_delivery_ok = True
    paid_delivery_ok = True

    print("FREE FOLDER DELIVERY METHODS:")
    for folder in free_folders:
        if folder in FOLDER_TO_DELIVERY:
            config = FOLDER_TO_DELIVERY[folder]
            method = config.get('method', 'unknown')

            if method == 'bot' and config.get('server') == '1390050801136701642':
                print(f"  ✅ {folder:18s} → {method:8s} → Free Server ✅")
            else:
                print(f"  ❌ {folder:18s} → {method:8s} → WRONG DELIVERY!")
                free_delivery_ok = False
        else:
            print(f"  ❌ {folder:18s} → NOT CONFIGURED!")
            free_delivery_ok = False

    print("\nPAID FOLDER DELIVERY METHODS:")
    for folder in paid_folders:
        if folder in FOLDER_TO_DELIVERY:
            config = FOLDER_TO_DELIVERY[folder]
            method = config.get('method', 'unknown')

            if method == 'webhook' and 'url' in config:
                print(f"  ✅ {folder:18s} → {method:8s} → Paid Server ✅")
            else:
                print(f"  ❌ {folder:18s} → {method:8s} → WRONG DELIVERY!")
                paid_delivery_ok = False
        else:
            print(f"  ❌ {folder:18s} → NOT CONFIGURED!")
            paid_delivery_ok = False

    print("\n" + "=" * 60)
    if free_delivery_ok and paid_delivery_ok:
        print("🎉 DELIVERY CONFIGURATION VALIDATED - NO PREMIUM LEAKAGE! 🎉")
        return True
    else:
        print("⚠️  DELIVERY CONFIGURATION HAS ISSUES!")
        return False

def main():
    """Run complete validation"""
    print("🚀 TELEGRAM TO DISCORD ROUTING VALIDATION")
    print("🎯 CRITICAL: Ensuring FREE content never leaks to premium")
    print("=" * 60)

    # Test routing logic
    routing_ok = test_routing_scenarios()

    # Test delivery configuration
    delivery_ok = validate_delivery_config()

    print("\n" + "=" * 60)
    print("FINAL VALIDATION RESULT")
    print("=" * 60)

    if routing_ok and delivery_ok:
        print("🎉 COMPLETE SYSTEM VALIDATION PASSED! 🎉")
        print("✅ FREE content is fully protected from premium leakage")
        print("✅ PAID content routes correctly to premium channels")
        print("✅ System ready for production")
        return True
    else:
        print("❌ VALIDATION FAILED!")
        print("⚠️  System needs fixes before production use")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)