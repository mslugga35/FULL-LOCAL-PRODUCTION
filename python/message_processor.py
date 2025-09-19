#!/usr/bin/env python3
import os
import json
import shutil
import time
from pathlib import Path
from datetime import datetime

def process_messages():
    inbox = Path('/root/inbox')
    queue = Path('/root/bots/message_queue')
    
    # Mapping based on ID patterns in filename
    mappings = {
        '1802': 'uatb',           # UATB messages
        '318': 'diamond',         # Diamond/Chamba messages  
        '116': 'free_cappers',    # Free cappers
        '1159': 'exclusive_cappers',  # Exclusive
        '1156': 'leaked_cappers'      # Leaked
    }
    
    # Create folders
    for folder in mappings.values():
        (queue / folder).mkdir(parents=True, exist_ok=True)
    
    # Process files
    moved = 0
    for file in inbox.glob('*'):
        if file.is_file():
            filename = file.name
            for pattern, folder in mappings.items():
                if pattern in filename:
                    dest = queue / folder / filename
                    shutil.move(str(file), str(dest))
                    print(f'[{datetime.now().strftime("%H:%M:%S")}] Moved {filename} to {folder}')
                    moved += 1
                    break
    
    if moved > 0:
        print(f'Moved {moved} files total')
    
    return moved

if __name__ == '__main__':
    print('Starting message processor...')
    while True:
        try:
            process_messages()
            time.sleep(5)
        except Exception as e:
            print(f'Error: {e}')
            time.sleep(10)
