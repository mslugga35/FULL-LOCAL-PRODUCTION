#!/usr/bin/env python3
"""
Discord Consumer Bot - Improved with Rate Limiting
Reads from inbox/queue and sends to Discord with proper throttling
"""

import os
import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import requests
from google.cloud import vision

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/bots/discord-consumer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
QUEUE_DIR = os.getenv("QUEUE_DIR", "/root/bots/C:\\Users\\mpmmo\\message_queue")
INBOX_DIR = os.getenv("INBOX_DIR", "/root/inbox")
PROCESSED_DIR = os.path.join(QUEUE_DIR, "processed")
CHECK_INTERVAL = 5  # seconds
RATE_LIMIT_DELAY = 1.2  # seconds between webhook sends

# Google Vision setup
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/root/bots/google-vision-key.json'
vision_client = None
try:
    vision_client = vision.ImageAnnotatorClient()
    logger.info("Google Vision API initialized")
except Exception as e:
    logger.warning(f"Google Vision not available: {e}")

# Discord webhook mappings with rate limit tracking
DISCORD_WEBHOOKS = {
    "free_cappers": {
        "url": os.getenv("WEBHOOK_FREE_CAPPERS", "https://discord.com/api/webhooks/1412519047387680849/0S_gU6yUwm5EnSz8IWeBAUTmq0WbCukWzKBBkt_zNPv8nkXiieHFviP_POsk4YGXY7nb"),
        "last_sent": 0,
        "retry_after": 0
    },
    "leaked_cappers": {
        "url": os.getenv("WEBHOOK_LEAKED_CAPPERS", "https://discord.com/api/webhooks/1412519200806928384/K2wGb9L1RKiAywc0ZW1vVJD-nfrK-tLqLsqUvo5I8aTHsIanPAQUn-2dXrKcv5zmJC0g"),
        "last_sent": 0,
        "retry_after": 0
    },
    "exclusive_cappers": {
        "url": os.getenv("WEBHOOK_EXCLUSIVE_CAPPERS", "https://discord.com/api/webhooks/1412519326086463620/ZkHIUOlVXlgKbWWgFu9WtbZqC6VONTliNxHpsFdOw5uNIwDlFgL2MMQ18_W9nGj07GKb"),
        "last_sent": 0,
        "retry_after": 0
    },
    "paid_uatb": {
        "url": os.getenv("WEBHOOK_PAID_UATB", "https://discord.com/api/webhooks/1412519461319348414/cc_yo1Cowss9O4oLCBWv9ttMCkwz68CMirfJ38YNKdr8MRUy37AuhNS08b8H1LK4P8fE"),
        "last_sent": 0,
        "retry_after": 0
    },
    "paid_diamond": {
        "url": os.getenv("WEBHOOK_PAID_DIAMOND", "https://discord.com/api/webhooks/1412519542999089323/51TLxfKO1RP5oklvagJOfcdkXz4mt8wZ25qAmrphrD0GPxJrC8E6k98VglV2K1S19Nup"),
        "last_sent": 0,
        "retry_after": 0
    },
    "paid_cappers": {
        "url": os.getenv("WEBHOOK_PAID_CAPPERS", "https://discord.com/api/webhooks/1412519618005700760/AgYkqG16xaBsX8mxL7vZrgGxbEoIkSJoPa5eX_06yEx_tLCkCCcsjSXotM9EZtXhyZvP"),
        "last_sent": 0,
        "retry_after": 0
    },
}

# Track processed messages
processed_messages = set()

def load_processed_messages():
    """Load already processed message IDs"""
    try:
        processed_file = os.path.join(QUEUE_DIR, "processed_today.json")
        if os.path.exists(processed_file):
            with open(processed_file, 'r') as f:
                data = json.load(f)
                today = datetime.now().strftime("%Y-%m-%d")
                if data.get("date") == today:
                    return set(data.get("messages", []))
    except Exception as e:
        logger.error(f"Error loading processed messages: {e}")
    return set()

def save_processed_messages():
    """Save processed message IDs"""
    try:
        processed_file = os.path.join(QUEUE_DIR, "processed_today.json")
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "messages": list(processed_messages)
        }
        with open(processed_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving processed messages: {e}")

def perform_ocr(image_path):
    """Perform OCR on an image using Google Vision"""
    if not vision_client:
        return None
    
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = vision_client.text_detection(image=image)
        
        if response.text_annotations:
            full_text = response.text_annotations[0].description
            return clean_ocr_text(full_text)
        
        return None
    except Exception as e:
        logger.error(f"OCR error for {image_path}: {e}")
        return None

def clean_ocr_text(text):
    """Clean and format OCR text for Discord"""
    if not text:
        return ""
    
    lines_to_remove = [
        "CAPPERS FREE",
        "HANDICAPPERS LEAKED",
        "@cappersfree",
        "Join our",
        "Subscribe to",
        "DM for",
        "➖" * 5
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or any(spam in line for spam in lines_to_remove):
            continue
        cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines)
    if len(result) > 1800:
        result = result[:1800] + "..."
    
    return result

async def send_to_discord_webhook(webhook_info, content, embed=None, file_path=None):
    """Send message to Discord with rate limiting"""
    current_time = time.time()
    
    # Check rate limit
    if current_time < webhook_info["retry_after"]:
        wait_time = webhook_info["retry_after"] - current_time
        logger.info(f"Rate limited, waiting {wait_time:.1f}s")
        await asyncio.sleep(wait_time)
        current_time = time.time()
    
    # Check per-webhook throttle
    time_since_last = current_time - webhook_info["last_sent"]
    if time_since_last < RATE_LIMIT_DELAY:
        wait_time = RATE_LIMIT_DELAY - time_since_last
        await asyncio.sleep(wait_time)
        current_time = time.time()
    
    try:
        data = {}
        files = {}
        
        if content:
            data["content"] = content[:2000]
        
        if embed:
            data["embeds"] = [embed]
        
        # For paid channels, include the image
        if file_path and os.path.exists(file_path):
            if any(paid in webhook_info["url"] for paid in ["paid", "uatb", "diamond"]):
                files["file"] = open(file_path, "rb")
        
        response = requests.post(
            webhook_info["url"], 
            json=data if not files else None,
            data=data if files else None,
            files=files, 
            timeout=10
        )
        
        if files:
            files["file"].close()
        
        # Update last sent time
        webhook_info["last_sent"] = current_time
        
        if response.status_code == 204:
            logger.info(f"✓ Sent to Discord")
            return True
        elif response.status_code == 429:
            # Handle rate limit
            retry_after = float(response.headers.get('Retry-After', 5))
            webhook_info["retry_after"] = current_time + retry_after
            logger.warning(f"Rate limited for {retry_after}s")
            return False
        else:
            logger.error(f"Discord webhook error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Discord send error: {e}")
        return False

async def process_message_file(json_path):
    """Process a single message JSON file"""
    try:
        with open(json_path, 'r') as f:
            message_data = json.load(f)
        
        message_id = message_data.get("message_id", Path(json_path).stem)
        if False: # Temporarily disabled for resend
            return
        
        folder_name = Path(json_path).parent.name
        webhook_info = DISCORD_WEBHOOKS.get(folder_name)
        
        if not webhook_info:
            logger.warning(f"No webhook for folder: {folder_name}")
            return
        
        chat_title = message_data.get("chat_title", "Unknown")
        text = message_data.get("text", "")
        has_media = message_data.get("has_media", False)
        needs_ocr = message_data.get("needs_ocr", False)
        
        content = f"**[{chat_title}]**\n"
        media_path = None
        ocr_text = None
        
        if has_media:
            media_file = message_data.get("media_file")
            if media_file:
                media_path = os.path.join(Path(json_path).parent, media_file)
                if not os.path.exists(media_path):
                    base_name = Path(json_path).stem
                    for ext in ['.jpg', '.png', '.jpeg', '.webp']:
                        test_path = os.path.join(Path(json_path).parent, base_name + ext)
                        if os.path.exists(test_path):
                            media_path = test_path
                            break
                
                if needs_ocr and media_path and os.path.exists(media_path):
                    logger.info(f"Performing OCR on {media_path}")
                    ocr_text = perform_ocr(media_path)
                    if ocr_text:
                        logger.info(f"OCR extracted {len(ocr_text)} chars")
        
        if text:
            content += text[:1500] + "\n"
        
        if ocr_text and "paid" not in folder_name:
            content += f"\n**📸 Screenshot Text:**\n```\n{ocr_text}\n```"
        
        embed = None
        if ocr_text and "paid" in folder_name:
            embed = {
                "title": "📸 OCR Text",
                "description": ocr_text[:4000],
                "color": 0x00ff00,
                "timestamp": datetime.now().isoformat()
            }
        
        success = await send_to_discord_webhook(webhook_info, content, embed, media_path)
        
        if success:
            processed_messages.add(message_id)
            try:
                processed_folder = os.path.join(PROCESSED_DIR, folder_name)
                os.makedirs(processed_folder, exist_ok=True)
                
                os.rename(json_path, os.path.join(processed_folder, Path(json_path).name))
                
                if media_path and os.path.exists(media_path):
                    os.rename(media_path, os.path.join(processed_folder, Path(media_path).name))
                    
            except Exception as e:
                logger.error(f"Error moving files: {e}")
                
    except Exception as e:
        logger.error(f"Error processing {json_path}: {e}")

async def check_queues():
    """Check all queue folders for new messages"""
    dirs_to_check = []
    
    if os.path.exists(QUEUE_DIR):
        for folder in os.listdir(QUEUE_DIR):
            folder_path = os.path.join(QUEUE_DIR, folder)
            if os.path.isdir(folder_path) and folder != "processed":
                dirs_to_check.append(folder_path)
    
    if os.path.exists(INBOX_DIR):
        dirs_to_check.append(INBOX_DIR)
    
    for dir_path in dirs_to_check:
        try:
            json_files = list(Path(dir_path).glob("*.json"))
            
            for json_file in json_files:
                if json_file.name == "processed_today.json":
                    continue
                    
                logger.info(f"Processing: {json_file}")
                await process_message_file(str(json_file))
                
                # Small delay between messages
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error checking {dir_path}: {e}")

async def main():
    """Main loop"""
    logger.info("=" * 50)
    logger.info("DISCORD CONSUMER BOT - IMPROVED")
    logger.info("=" * 50)
    logger.info(f"Queue Dir: {QUEUE_DIR}")
    logger.info(f"Inbox Dir: {INBOX_DIR}")
    logger.info(f"OCR: {'Enabled' if vision_client else 'Disabled'}")
    logger.info(f"Rate Limit Delay: {RATE_LIMIT_DELAY}s")
    logger.info("=" * 50)
    
    global processed_messages
    processed_messages = load_processed_messages()
    logger.info(f"Loaded {len(processed_messages)} processed messages")
    
    while True:
        try:
            await check_queues()
            
            if len(processed_messages) % 10 == 0:
                save_processed_messages()
                
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
        save_processed_messages()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()