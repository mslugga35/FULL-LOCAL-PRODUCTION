#!/usr/bin/env python3
"""
Restart the forwarder process to load new formatting code
"""
import subprocess
import sys
import time
from pathlib import Path

# Sentinel for "the process check itself could not run". It is deliberately NOT None
# and NOT a pid, because the bug this file used to have was reading one as the other.
UNKNOWN = object()


def _run(argv, use_shell=False):
    """Run a command, returning stdout or None if it could not run at all."""
    try:
        result = subprocess.run(argv, capture_output=True, text=True, shell=use_shell)
    except Exception:
        return None
    if result.returncode != 0:
        return None
    out = result.stdout or ''
    return out if out.strip() else None


def list_python_command_lines():
    """Every running python.exe as (pid, command_line), or None if we could not look.

    None means "the enumeration failed", which is NOT the same as "nothing is
    running" -- see find_forwarder_process.

    wmic was removed in Windows 11 build 26200, so it is tried first only for older
    boxes and PowerShell's CIM query is the real path now.
    """
    # 1. wmic (absent on Win11 26200+, kept for older hosts)
    out = _run(['wmic', 'process', 'where', 'name="python.exe"',
                'get', 'ProcessId,CommandLine'], use_shell=True)
    if out:
        rows = []
        for line in out.splitlines():
            line = line.strip()
            if not line or line.startswith('CommandLine'):
                continue
            parts = line.rsplit(None, 1)
            if len(parts) == 2 and parts[1].isdigit():
                rows.append((parts[1], parts[0]))
        if rows:
            return rows

    # 2. PowerShell CIM -- works on current Windows, and gives us CommandLine,
    #    which tasklist cannot provide.
    out = _run(['powershell', '-NoProfile', '-Command',
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" "
                "| ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"])
    if out is None:
        return None

    rows = []
    for line in out.splitlines():
        if '\t' not in line:
            continue
        pid, _, cmd = line.partition('\t')
        pid = pid.strip()
        if pid.isdigit():
            rows.append((pid, cmd))
    return rows


def find_forwarder_process():
    """PID string if the forwarder is running, None if it is not, UNKNOWN if we could not tell.

    The three states are the entire point. This function used to return None both
    when no forwarder was running and when the lookup failed, and main() started a
    new forwarder on None. After wmic was removed from Windows the lookup failed
    every time, so running this script would have launched a SECOND forwarder on
    top of the live one -- two processes polling the same Telegram token, which
    surfaces as a 409 "another process has the token" conflict and double-posted
    picks.
    """
    rows = list_python_command_lines()
    if rows is None:
        return UNKNOWN
    for pid, cmd in rows:
        if 'forwarder.py' in (cmd or ''):
            return pid
    return None


def kill_process(pid):
    """Kill process by PID"""
    try:
        subprocess.run(['taskkill', '/F', '/PID', pid], check=True, capture_output=True)
        print(f"OK Killed forwarder process {pid}")
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

        print(f"OK Started forwarder with PID: {proc.pid}")
        return True
    except Exception as e:
        print(f"Error starting forwarder: {e}")
        return False


def main():
    if '--self-test' in sys.argv:
        return self_test()

    print("Restarting forwarder to load new formatting code...")

    pid = find_forwarder_process()

    if pid is UNKNOWN:
        # Refuse rather than guess. Starting here is what creates the duplicate.
        print("ABORT: could not enumerate running processes, so it is unknown whether")
        print("       a forwarder is already running. Refusing to start a second one.")
        print("       Check manually:")
        print("         powershell \"Get-CimInstance Win32_Process -Filter \\\"Name='python.exe'\\\" | \"")
        print("         Select-Object ProcessId,CommandLine\"")
        return 2

    if pid:
        print(f"Found forwarder process: PID {pid}")
        if kill_process(pid):
            print("Waiting 2 seconds for cleanup...")
            time.sleep(2)
        else:
            print("ABORT: found a running forwarder but could not kill it.")
            print("       Starting another one would duplicate it.")
            return 3
    else:
        print("No existing forwarder process found")

    if start_forwarder():
        print("OK Forwarder restarted successfully!")
        return 0

    print("FAIL Failed to start forwarder")
    return 1


def self_test():
    """Prove the three states stay distinct. Starts and kills nothing."""
    failures = []

    def check(cond, what):
        print(f"  {'ok  ' if cond else 'FAIL'} {what}")
        if not cond:
            failures.append(what)

    original = globals()['list_python_command_lines']
    try:
        globals()['list_python_command_lines'] = lambda: None
        check(find_forwarder_process() is UNKNOWN,
              "a failed enumeration is UNKNOWN, not 'no forwarder'")

        globals()['list_python_command_lines'] = lambda: []
        check(find_forwarder_process() is None,
              "an empty process list really is 'no forwarder'")

        globals()['list_python_command_lines'] = lambda: [('123', 'python.exe src/forwarder.py')]
        check(find_forwarder_process() == '123', "a running forwarder is found by pid")

        globals()['list_python_command_lines'] = lambda: [('9', 'python.exe something_else.py')]
        check(find_forwarder_process() is None,
              "an unrelated python process is not the forwarder")

        check(UNKNOWN is not None, "UNKNOWN can never be confused with None")
    finally:
        globals()['list_python_command_lines'] = original

    if failures:
        print(f"SELFTEST FAILED ({len(failures)})")
        return 1
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
