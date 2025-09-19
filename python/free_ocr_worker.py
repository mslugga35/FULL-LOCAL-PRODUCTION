#!/usr/bin/env python3
import os, re, time, json, shutil
from datetime import datetime

# OCR settings
USE_TESS = True

QUEUE_DIRS = [
    '/root/bots/message_queue/free_cappers',
    '/root/bots/message_queue/leaked_cappers',
    '/root/bots/message_queue/exclusive_cappers',
]
PROCESSED_BASE = '/root/bots/message_queue/processed'

def ocr_image(path):
    text = ''
    try:
        if USE_TESS:
            import pytesseract
            from PIL import Image
            text = pytesseract.image_to_string(Image.open(path)) or ''
    except Exception as e:
        print(f'[free-ocr] OCR error: {e}')
    return text.strip()

def ai_clean(raw_text):
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    capper = 'Unknown'
    
    for l in lines[:5]:
        if '@' in l or 'From:' in l:
            capper = re.sub(r'[^@A-Za-z0-9_ .-]', '', l).strip()
            capper = capper.replace('From:', '').strip()
            break
    
    picks = []
    for l in lines:
        if re.search(r'(ML|Over|Under|MLB|NBA|NHL|NFL|\+|\-|spread|total)', l, re.I):
            picks.append(re.sub(r'\s+', ' ', l))
    
    if not picks and lines:
        picks = lines[:3]
    
    picks = picks[:8]
    
    output = f'Capper: {capper}\nPicks:'
    for p in picks:
        output += f'\n- {p}'
    
    return output

def find_sibling_media(dirpath, json_base):
    base = json_base[:-5]
    candidates = []
    for f in os.listdir(dirpath):
        if f == json_base:
            continue
        if not re.search(r'\.(jpg|jpeg|png|webp|gif)$', f, re.I):
            continue
        if f.startswith(base):
            candidates.append(os.path.join(dirpath, f))
    return sorted(candidates)

def process_one(queue_dir, jf):
    jp = os.path.join(queue_dir, jf)
    try:
        with open(jp) as f:
            payload = json.load(f)
    except Exception as e:
        print(f'[free-ocr] Bad JSON {jp}: {e}')
        return
    
    media = find_sibling_media(queue_dir, jf)
    raw_text = (payload.get('caption', '') + '\n' + payload.get('text', '')).strip()
    
    if media:
        ocr_text = ocr_image(media[0])
        if ocr_text:
            raw_text = (raw_text + '\n' + ocr_text).strip()
    
    cleaned = ai_clean(raw_text).strip()
    base = jf[:-5]
    clean_path = os.path.join(queue_dir, f'{base}.clean.txt')
    
    with open(clean_path, 'w') as f:
        f.write(cleaned + '\n')
    
    print(f'[free-ocr] Created {clean_path}')

def ensure_dirs():
    os.makedirs(PROCESSED_BASE, exist_ok=True)
    for q in QUEUE_DIRS:
        os.makedirs(q, exist_ok=True)
        os.makedirs(os.path.join(PROCESSED_BASE, os.path.basename(q)), exist_ok=True)

def main():
    print('=== Free OCR Worker Started ===')
    ensure_dirs()
    while True:
        for q in QUEUE_DIRS:
            try:
                files = [f for f in os.listdir(q) if f.endswith('.json')]
                for jf in sorted(files):
                    base = jf[:-5]
                    clean = os.path.join(q, f'{base}.clean.txt')
                    if not os.path.exists(clean):
                        process_one(q, jf)
            except Exception as e:
                print(f'[free-ocr] Error: {e}')
        time.sleep(2)

if __name__ == '__main__':
    main()
