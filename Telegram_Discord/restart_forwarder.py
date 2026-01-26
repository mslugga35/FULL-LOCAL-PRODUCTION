#!/usr/bin/env python3
"""
Restart the forwarder process to load new formatting code
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def find_forwarder_process():
    """Find running forwarder process by checking logs"""
    try:
        # Check if forwarder.py is in running processes
        result = subprocess.run(['wmic', 'process', 'where', 'name="python.exe"', 'get', 'ProcessId,CommandLine'],
                              capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'forwarder.py' in line:
                    # Extract PID from the line
                    parts = line.strip().split()
                    if parts:
                        return parts[-1]  # Last part should be PID
        return None
    except Exception as e:
        print(f"Error finding forwarder process: {e}")
        return None

def kill_process(pid):
    """Kill process by PID"""
    try:
        subprocess.run(['taskkill', '/F', '/PID', pid], check=True, capture_output=True)
        print(f"✓ Killed forwarder process {pid}")
        return True
    except Exception as e:
        print(f"Error killing process {pid}: {e}")
        return False

def start_forwarder():
    """Start the forwarder in a new process"""
    try:
        script_dir = Path(__file__).parent
        forwarder_script = script_dir / "src" / "forwarder.py"

        print(f"Starting forwarder: {forwarder_script}")

        # Start forwarder in background
        proc = subprocess.Popen([
            sys.executable, str(forwarder_script)
        ], cwd=str(script_dir))

        print(f"✓ Started forwarder with PID: {proc.pid}")
        return True
    except Exception as e:
        print(f"Error starting forwarder: {e}")
        return False

def main():
    print("Restarting forwarder to load new formatting code...")

    # Find and kill existing forwarder
    pid = find_forwarder_process()
    if pid and pid.isdigit():
        print(f"Found forwarder process: PID {pid}")
        if kill_process(pid):
            print("Waiting 2 seconds for cleanup...")
            time.sleep(2)
    else:
        print("No existing forwarder process found")

    # Start new forwarder
    if start_forwarder():
        print("✓ Forwarder restarted successfully!")
        print("New messages will now use enhanced CAPPERS FREE filtering")
    else:
        print("✗ Failed to start forwarder")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())