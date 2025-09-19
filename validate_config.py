#!/usr/bin/env python3
"""
Configuration Validator for Telegram to Discord System
Quick validation of routing_config.json and environment setup.
"""

import json
import os
import sys
from pathlib import Path

def validate_config():
    """Validate routing configuration"""
    print("Validating routing_config.json...")

    try:
        with open('routing_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        print(f"[OK] Configuration loaded successfully")
        print(f"  Version: {config.get('version', 'unknown')}")
        print(f"  Base Path: {config.get('windows_base_path', 'NOT SET')}")

        # Check required keys
        required_keys = ['windows_base_path', 'telegram_channels', 'discord_forwarder_integration', 'queue_management']
        for key in required_keys:
            if key in config:
                print(f"  [OK] {key}")
            else:
                print(f"  [MISSING] {key}")
                return False

        # Check channels
        channels = config.get('telegram_channels', {})
        enabled_channels = [ch for ch in channels.values() if ch.get('enabled', False)]

        print(f"\nTelegram Channels:")
        print(f"  Total configured: {len(channels)}")
        print(f"  Enabled: {len(enabled_channels)}")

        for channel_id, channel_config in channels.items():
            status = "[ENABLED]" if channel_config.get('enabled', False) else "[DISABLED]"
            display_name = channel_config.get('name', 'Unknown')  # Use name instead of display_name to avoid emojis
            queue_path = channel_config.get('queue_path', 'No path')
            print(f"  {status} {display_name} -> {queue_path}")

        # Check paths
        base_path = Path(config.get('windows_base_path', ''))
        if base_path.is_absolute():
            print(f"[OK] Base path is absolute: {base_path}")
        else:
            print(f"[ERROR] Base path should be absolute: {base_path}")

        return True

    except FileNotFoundError:
        print("[ERROR] routing_config.json not found")
        return False
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in routing_config.json: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error validating config: {e}")
        return False

def validate_environment():
    """Validate environment variables"""
    print("\nValidating environment variables...")

    required_vars = [
        'TELEGRAM_STRING_SESSION',
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH',
        'DISCORD_BOT_TOKEN'
    ]

    all_present = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  [OK] {var}: {'*' * min(len(value), 20)}...")
        else:
            print(f"  [MISSING] {var}: NOT SET")
            all_present = False

    return all_present

def validate_files():
    """Validate required files exist"""
    print("\nValidating required files...")

    required_files = [
        'system_controller.py',
        'telegram_collector_updated.py',
        'discord_forwarder_production.py',
        'routing_config.json'
    ]

    all_present = True

    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"  [OK] {file_name} ({size_kb:.1f} KB)")
        else:
            print(f"  [MISSING] {file_name}: NOT FOUND")
            all_present = False

    return all_present

def validate_directories():
    """Validate directory structure"""
    print("\nValidating directory structure...")

    # Create basic directories
    dirs_to_check = ['logs', 'message_queue']

    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"  [CREATED] {dir_name}")
        else:
            print(f"  [OK] Exists: {dir_name}")

    # Check config-based directories
    try:
        with open('routing_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        base_path = Path(config.get('windows_base_path', 'message_queue'))
        if not base_path.exists():
            print(f"  [WARNING] Base path does not exist: {base_path}")
            return False

        for channel_id, channel_config in config.get('telegram_channels', {}).items():
            if not channel_config.get('enabled', False):
                continue

            queue_path = channel_config.get('queue_path', '')
            channel_dir = base_path / queue_path

            if not channel_dir.exists():
                channel_dir.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] Channel dir: {queue_path}")
            else:
                print(f"  [OK] Channel dir exists: {queue_path}")

    except Exception as e:
        print(f"  [ERROR] Error checking channel directories: {e}")
        return False

    return True

def main():
    """Main validation"""
    print("=" * 60)
    print("TELEGRAM TO DISCORD SYSTEM VALIDATION")
    print("=" * 60)

    results = {
        'config': validate_config(),
        'environment': validate_environment(),
        'files': validate_files(),
        'directories': validate_directories()
    }

    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    all_passed = True
    for check, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} - {check.title()}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("ALL VALIDATIONS PASSED")
        print("System is ready for production!")
        print("\nNext steps:")
        print("1. Run: START_SYSTEM_CONTROLLER.bat")
        print("2. Monitor: START_PRODUCTION_MONITOR.bat")
    else:
        print("SOME VALIDATIONS FAILED")
        print("Please fix the issues above before starting the system.")

    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())