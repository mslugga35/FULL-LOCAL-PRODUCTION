#!/usr/bin/env python3
"""
Consensus Pipeline Scheduler
- Mon-Fri 4-7 PM EST: every 15 minutes
- All other times: every hour
"""

import subprocess
import sys
import time
import os
from datetime import datetime, timedelta
import pytz

# Config
EST = pytz.timezone('America/New_York')
PIPELINE_SCRIPT = os.path.join(os.path.dirname(__file__), 'run_consensus_pipeline.py')
PEAK_START = 16  # 4 PM
PEAK_END = 19    # 7 PM (runs until 6:45)
PEAK_INTERVAL = 15 * 60  # 15 minutes in seconds
NORMAL_INTERVAL = 60 * 60  # 1 hour in seconds

def is_peak_hours():
    """Check if current time is Mon-Fri 4-7 PM EST"""
    now = datetime.now(EST)
    weekday = now.weekday()  # 0=Mon, 6=Sun
    hour = now.hour
    
    is_weekday = weekday < 5  # Mon-Fri
    is_peak_time = PEAK_START <= hour < PEAK_END
    
    return is_weekday and is_peak_time

def run_pipeline():
    """Execute the consensus pipeline"""
    now = datetime.now(EST)
    print(f"\n{'='*60}")
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')} EST] Running consensus pipeline...")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, PIPELINE_SCRIPT],
            cwd=os.path.dirname(PIPELINE_SCRIPT),
            capture_output=False,
            timeout=300  # 5 min timeout
        )
        print(f"Pipeline completed with exit code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print("ERROR: Pipeline timed out after 5 minutes")
    except Exception as e:
        print(f"ERROR running pipeline: {e}")

def get_next_run_delay():
    """Calculate seconds until next run based on time of day"""
    now = datetime.now(EST)
    
    if is_peak_hours():
        # During peak: run every 15 min aligned to :00, :15, :30, :45
        minutes = now.minute
        next_slot = ((minutes // 15) + 1) * 15
        if next_slot >= 60:
            next_slot = 0
            delay = (60 - minutes) * 60 - now.second
        else:
            delay = (next_slot - minutes) * 60 - now.second
        
        mode = "PEAK (every 15 min)"
    else:
        # Off-peak: run every hour at :00
        delay = (60 - now.minute) * 60 - now.second
        mode = "NORMAL (every hour)"
    
    return max(delay, 60), mode  # minimum 60 sec delay

def main():
    print("""
============================================================
         CONSENSUS PIPELINE SCHEDULER                        
                                                              
  Schedule:                                                   
  - Mon-Fri 4-7 PM EST: every 15 minutes                     
  - All other times: every hour                              
============================================================
""", flush=True)
    
    # Run immediately on start
    run_pipeline()
    
    while True:
        delay, mode = get_next_run_delay()
        next_run = datetime.now(EST).replace(microsecond=0) + timedelta(seconds=delay)
        
        print(f"\n[{datetime.now(EST).strftime('%H:%M:%S')}] Mode: {mode}")
        print(f"Next run at: {next_run.strftime('%H:%M:%S')} EST ({delay//60} min {delay%60} sec)")
        
        time.sleep(delay)
        run_pipeline()

if __name__ == '__main__':
    main()
