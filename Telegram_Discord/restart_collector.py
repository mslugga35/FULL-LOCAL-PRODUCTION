#!/usr/bin/env python3
"""
Restart the Telegram collector process
"""
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def find_collector_process():
    """Find running collector process"""
    try:
        # Use tasklist on Windows to find Python processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                              capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'python.exe' in line and 'telegram_collector' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]  # PID
        return None
    except Exception as e:
        print(f"Error finding process: {e}")
        return None

def kill_process(pid):
    """Kill process by PID"""
    try:
        subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
        print(f"✓ Killed process {pid}")
        return True
    except Exception as e:
        print(f"Error killing process {pid}: {e}")
        return False

def start_collector():
    """Start the collector in a new process"""
    try:
        script_dir = Path(__file__).parent
        collector_script = script_dir / "src" / "telegram_collector.py"

        print(f"Starting collector: {collector_script}")

        # Start collector in background
        proc = subprocess.Popen([
            sys.executable, str(collector_script)
        ], cwd=str(script_dir))

        print(f"✓ Started collector with PID: {proc.pid}")
        return True
    except Exception as e:
        print(f"Error starting collector: {e}")
        return False

def main():
    print("=" * 50)
    print("Telegram Collector Restart Script")
    print("=" * 50)

    # Find and kill existing collector
    print("Looking for existing collector process...")
    pid = find_collector_process()

    if pid:
        print(f"Found collector process: PID {pid}")
        if kill_process(pid):
            print("Waiting 3 seconds for cleanup...")
            time.sleep(3)
    else:
        print("No existing collector process found")

    # Start new collector
    print("Starting new collector...")
    if start_collector():
        print("✓ Collector restart complete!")
        print("Check logs/collector.log for status")
    else:
        print("✗ Failed to start collector")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())