#!/usr/bin/env python3
"""
Free Picks to Google Docs Exporter
Aggregates all free channel picks from sent_archive and updates a Google Doc hourly.
"""

import os
import sys
import json
import logging
import time
import random
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from collections import defaultdict
import pytz

# Google API imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import google.generativeai as genai
    from PIL import Image
except ImportError:
    print("❌ Google API libraries not installed!")
    print("Run: pip install google-api-python-client google-auth google-generativeai pillow")
    sys.exit(1)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import SMART recap/result detection (replaces old pattern-based filter)
from src.utils.smart_recap_filter import should_filter_message

# Import vision formatter for structured picks
try:
    from src.utils.vision_formatter import get_vision_processed_picks, format_structured_picks
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Vision formatter not available, using OCR fallback")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gdocs_exporter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(exist_ok=True)
# Read from BOTH sources for complete real-time + archived picks
MESSAGE_QUEUE_DIR = BASE_DIR / "message_queue"
SENT_ARCHIVE_DIR = BASE_DIR / "sent_archive"
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")  # Default/fallback doc
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")  # Optional folder for daily docs
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/New_York"))

# Daily doc tracking file
DAILY_DOCS_FILE = STATE_DIR / "daily_docs.json"

# Free channels configuration
# Only include CAPPERS FREE channel
FREE_CHANNELS = {
    "free_cappers": {
        "name": "CAPPERS FREE💥",
        "emoji": "🔥",
        "folder": "free_cappers"
    }
}

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

# Gemini rate limiting (10 requests/minute)
_gemini_request_times = []
_gemini_max_requests_per_minute = 10

# OCR cache directory
OCR_CACHE_DIR = BASE_DIR / "ocr_cache"
OCR_CACHE_DIR.mkdir(exist_ok=True)


def load_daily_docs() -> dict:
    """Load daily doc ID tracking from JSON file"""
    if DAILY_DOCS_FILE.exists():
        try:
            with open(DAILY_DOCS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_daily_docs(docs: dict):
    """Save daily doc ID tracking to JSON file"""
    with open(DAILY_DOCS_FILE, 'w') as f:
        json.dump(docs, f, indent=2)


class GoogleDocsExporter:
    """Handles exporting picks to Google Docs with daily rotation"""

    def __init__(self):
        self.credentials = None
        self.docs_service = None
        self.drive_service = None
        self._authenticate()
        self.daily_docs = load_daily_docs()

    def _authenticate(self):
        """Authenticate with Google APIs using service account"""
        if not GOOGLE_CREDENTIALS_PATH:
            raise ValueError("GOOGLE_CREDENTIALS_PATH not set in .env")

        if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
            raise FileNotFoundError(f"Credentials file not found: {GOOGLE_CREDENTIALS_PATH}")

        logger.info(f"Authenticating with credentials: {GOOGLE_CREDENTIALS_PATH}")

        self.credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=SCOPES
        )

        self.docs_service = build('docs', 'v1', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)

        logger.info("✅ Authenticated with Google APIs")

    def get_or_create_daily_doc(self, date_str: str = None) -> str:
        """
        Get or create a Google Doc for the specified date.
        Returns doc ID for the day, creating one if needed.
        
        Args:
            date_str: Date in YYYYMMDD format (default: today)
        
        Returns:
            Google Doc ID for the day
        """
        if date_str is None:
            date_str = datetime.now(TIMEZONE).strftime("%Y%m%d")
        
        # Check if we already have a doc for this date
        if date_str in self.daily_docs:
            doc_id = self.daily_docs[date_str]
            logger.info(f"Using existing doc for {date_str}: {doc_id}")
            return doc_id
        
        # If no folder ID configured, use the default doc
        if not GOOGLE_DRIVE_FOLDER_ID:
            logger.info(f"No GOOGLE_DRIVE_FOLDER_ID set, using default doc: {GOOGLE_DOC_ID}")
            return GOOGLE_DOC_ID
        
        # Create a new document for today
        try:
            date_formatted = datetime.strptime(date_str, "%Y%m%d").strftime("%B %d, %Y")
            doc_title = f"Free Picks - {date_formatted}"
            
            # Create the document
            doc = self.docs_service.documents().create(body={
                'title': doc_title
            }).execute()
            
            new_doc_id = doc.get('documentId')
            
            # Move to the picks folder if specified
            if GOOGLE_DRIVE_FOLDER_ID:
                # Get current parents
                file = self.drive_service.files().get(
                    fileId=new_doc_id,
                    fields='parents'
                ).execute()
                previous_parents = ",".join(file.get('parents', []))
                
                # Move to new folder
                self.drive_service.files().update(
                    fileId=new_doc_id,
                    addParents=GOOGLE_DRIVE_FOLDER_ID,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()
            
            # Save to tracking
            self.daily_docs[date_str] = new_doc_id
            save_daily_docs(self.daily_docs)
            
            logger.info(f"✅ Created new doc for {date_str}: {new_doc_id}")
            logger.info(f"📄 https://docs.google.com/document/d/{new_doc_id}/edit")
            
            return new_doc_id
            
        except HttpError as error:
            logger.error(f"❌ Error creating daily doc: {error}")
            # Fall back to default doc
            return GOOGLE_DOC_ID

    def update_document(self, content: str, doc_id: str = None):
        """Update Google Doc with new content"""
        if doc_id is None:
            doc_id = GOOGLE_DOC_ID
        
        if not doc_id:
            raise ValueError("No doc_id provided and GOOGLE_DOC_ID not set in .env")

        try:
            # Clear existing content
            doc = self.docs_service.documents().get(documentId=doc_id).execute()

            # Get current document length
            content_length = doc.get('body').get('content')[-1].get('endIndex', 1)

            # Build requests list
            requests = []

            # Only delete content if document has more than just the required first character
            if content_length > 2:
                requests.append({
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': content_length - 1
                        }
                    }
                })

            # Insert new content
            requests.append({
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': content
                }
            })

            # Execute batch update
            result = self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()

            logger.info(f"✅ Document updated successfully: {doc_id}")
            return doc_id  # Return the doc_id so caller knows which doc was updated

        except HttpError as error:
            logger.error(f"❌ Error updating document: {error}")
            return False


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from image using Google Gemini Vision (structured output)
    Args:
        image_path: Path to image file
    Returns:
        Extracted text formatted with proper structure or empty string if failed
    """
    global _gemini_request_times

    # Check cache first
    import hashlib
    image_name = Path(image_path).name
    cache_key = hashlib.md5(image_name.encode()).hexdigest()
    cache_file = OCR_CACHE_DIR / f"{cache_key}.txt"

    if cache_file.exists():
        try:
            cached_text = cache_file.read_text(encoding='utf-8')
            logger.info(f"OCR cache hit for {image_name} ({len(cached_text)} chars)")
            return cached_text
        except Exception as e:
            logger.warning(f"Failed to read cache for {image_name}: {e}")

    max_retries = 3
    base_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            # Rate limiting: Space out requests to 10 seconds apart (ultra-safe, 6/minute max)
            # Free tier allows 10 RPM, but we'll be conservative to avoid ANY 429 errors
            now = time.time()
            # Remove requests older than 60 seconds
            _gemini_request_times = [t for t in _gemini_request_times if now - t < 60]

            # If we have recent requests, ensure at least 10 seconds since last one
            if _gemini_request_times:
                last_request = max(_gemini_request_times)
                time_since_last = now - last_request
                if time_since_last < 10:
                    wait_time = 10 - time_since_last
                    logger.info(f"Rate limit pacing: waiting {wait_time:.1f}s before {Path(image_path).name}")
                    time.sleep(wait_time)
                    now = time.time()

            # Double-check: If we've made 10 requests in the last minute, wait
            _gemini_request_times = [t for t in _gemini_request_times if now - t < 60]
            if len(_gemini_request_times) >= _gemini_max_requests_per_minute:
                oldest_request = min(_gemini_request_times)
                wait_time = 60 - (now - oldest_request) + 1
                logger.warning(f"Rate limit exceeded, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                now = time.time()
                _gemini_request_times = [t for t in _gemini_request_times if now - t < 60]

            # Record this request
            _gemini_request_times.append(now)
            # Configure Gemini with your Google Cloud credentials
            genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY") or "")

            # Use Gemini 2.5 Flash (stable, production-ready, 10 RPM free tier)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Load image
            img = Image.open(image_path)

            # Prompt for structured extraction - MUST detect results vs new picks
            prompt = """Analyze this sports betting image and determine if it shows:
A) A NEW PICK (bet not yet placed or pending)
B) A RESULT/RECEIPT (bet already placed, showing Won/Lost/Settled status, final scores, payouts)

INDICATORS OF A RESULT (return "[RESULT_SCREENSHOT]" if ANY of these):
- Shows "Won", "Lost", "Push", "Settled", "Finished", "Graded", "Completed"
- Shows checkmarks (✅) or X marks (❌) next to picks
- Shows final game scores (like 94-102)
- Shows payout amounts ($XXX.XX Won, Profit, etc.)
- Shows "Placed:" with a past date
- Shows transaction history or bet receipts
- Shows celebration text like "on point", "cashed", "let's go"

If this is a RESULT screenshot, return ONLY: [RESULT_SCREENSHOT]

If this is a NEW PICK, extract the picks with:
- Capper name at top (if visible)
- Each sport as a section header
- Bullet points for each pick
- Preserve units/odds information

COMPLETELY IGNORE AND REMOVE:
- "Messages from AI" or "Messages from"
- "DM @cappersfree" or any social media handles
- App UI elements, navigation, timestamps, profile pics
- Telegram/Discord interface elements
- Any promotional text about contacting cappers

Example format for NEW PICKS:
BeezoWins VIP Picks

NFL Football:
• Bills -5.5 (2-Unit)

NBA:
• Magic -6.5 (2-Unit)

Return ONLY "[RESULT_SCREENSHOT]" for results, or clean picks for new bets."""

            # Generate structured response
            response = model.generate_content([prompt, img])

            if response.text:
                extracted_text = response.text.strip()
                logger.info(f"Gemini extracted {len(extracted_text)} chars from {Path(image_path).name}")

                # Save to cache
                try:
                    cache_file.write_text(extracted_text, encoding='utf-8')
                    logger.debug(f"Cached OCR result for {image_name}")
                except Exception as e:
                    logger.warning(f"Failed to cache OCR for {image_name}: {e}")

                return extracted_text
            else:
                return ""

        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error (429)
            if "429" in error_str or "quota" in error_str.lower():
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter: prevents retry storms
                    base_wait = base_delay * (2 ** attempt)
                    jitter = random.uniform(0, base_wait * 0.3)  # Add up to 30% jitter
                    delay = min(base_wait + jitter, 60)  # Cap at 60 seconds
                    logger.warning(f"Rate limit hit for {Path(image_path).name}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Gemini Vision rate limit exceeded after {max_retries} attempts for {image_path}")
                    return ""
            else:
                # Non-rate-limit error, don't retry
                logger.error(f"Gemini Vision failed for {image_path}: {e}")
                return ""

    return ""


class PicksAggregator:
    """Aggregates picks from both message_queue (real-time) and sent_archive (delivered)"""

    def __init__(self, date: str = None):
        """
        Initialize aggregator
        Args:
            date: Date string in YYYYMMDD format for sent_archive
        """
        if date is None:
            date = datetime.now(TIMEZONE).strftime("%Y%m%d")

        self.date = date
        self.queue_path = MESSAGE_QUEUE_DIR
        self.archive_path = SENT_ARCHIVE_DIR / date
        self.picks_by_channel: Dict[str, List[Dict]] = defaultdict(list)

    def load_picks(self) -> Tuple[int, int]:
        """
        Load all picks from BOTH message_queue (pending) and sent_archive (delivered)
        This ensures we get ALL picks in real-time, whether pending or already sent
        Returns:
            Tuple of (total_picks, total_channels_with_picks)
        """
        # We'll collect message IDs to avoid duplicates
        seen_message_ids = set()

        total_picks = 0
        channels_with_picks = 0

        for channel_key, channel_config in FREE_CHANNELS.items():
            folder_name = channel_config["folder"]
            picks = []
            # Use the date passed to constructor (self.date), not always today
            target_date = datetime.strptime(self.date, "%Y%m%d").replace(tzinfo=TIMEZONE).date()

            # Check TWO locations: message_queue (pending) and sent_archive (delivered)
            paths_to_check = [
                (self.queue_path / folder_name, "queue"),
                (self.archive_path / folder_name, "archive")
            ]

            for channel_path, source in paths_to_check:
                if not channel_path.exists():
                    continue

                # Load all JSON files from this location
                json_files = list(channel_path.glob("*.json"))

                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            pick_data = json.load(f)

                            # Get message ID to avoid duplicates
                            msg_id = pick_data.get('id')
                            if msg_id and msg_id in seen_message_ids:
                                continue  # Skip duplicate

                            # Filter: Only include picks from TODAY
                            ts_iso = pick_data.get('ts_iso', '')
                            if ts_iso:
                                try:
                                    pick_time = datetime.fromisoformat(ts_iso.replace('Z', '+00:00'))
                                    pick_date = pick_time.astimezone(TIMEZONE).date()

                                    # Only include if it's from the target date
                                    if pick_date == target_date:
                                        picks.append(pick_data)
                                        if msg_id:
                                            seen_message_ids.add(msg_id)
                                except Exception:
                                    # If can't parse date, include it anyway
                                    picks.append(pick_data)
                                    if msg_id:
                                        seen_message_ids.add(msg_id)
                            else:
                                # No timestamp, include it
                                picks.append(pick_data)
                                if msg_id:
                                    seen_message_ids.add(msg_id)

                    except Exception as e:
                        logger.error(f"Error reading {json_file}: {e}")
                        continue

            if not picks:
                continue

            # Sort picks by timestamp - use raw.date (actual Telegram time) for accurate sorting
            picks.sort(key=lambda x: x.get('raw', {}).get('date', x.get('ts_iso', '')))

            self.picks_by_channel[channel_key] = picks
            total_picks += len(picks)
            channels_with_picks += 1

            logger.info(f"✅ Loaded {len(picks)} picks from {channel_config['name']}")

        logger.info(f"📊 Total: {total_picks} picks from {channels_with_picks} channels")
        return total_picks, channels_with_picks

    def format_for_google_docs(self) -> str:
        """Format picks as clean text for Google Docs"""
        now = datetime.now(TIMEZONE)
        date_formatted = now.strftime("%B %d, %Y")
        time_formatted = now.strftime("%I:%M %p %Z")

        lines = []
        # Date marker for automated parsers (dailyai-picks uses this)
        date_marker = now.strftime("%Y-%m-%d")
        lines.append(f"[PICKS_DATE:{date_marker}]")
        lines.append("⚠️ Recaps/yesterday results are filtered. Only TODAY's picks below.")
        lines.append("")
        lines.append(f"FREE PICKS - {date_formatted}")
        lines.append(f"Last updated: {time_formatted}")
        lines.append("═" * 50)
        lines.append("")

        total_picks = 0
        total_picks_with_content = 0

        for channel_key, channel_config in FREE_CHANNELS.items():
            picks = self.picks_by_channel.get(channel_key, [])
            pick_count = len(picks)

            # We'll count picks with actual content later
            picks_with_content = 0

            # Channel header - we'll update the count after processing
            emoji = channel_config["emoji"]
            name = channel_config["name"]
            header_index = len(lines)
            lines.append("")  # Placeholder for header
            lines.append("─" * 50)

            if not picks:
                lines.append("No picks yet today.")
            else:
                for pick in picks:
                    # Parse timestamp - use raw.date (actual Telegram message time) not ts_iso (file save time)
                    raw_date = pick.get('raw', {}).get('date', '')
                    ts_iso = pick.get('ts_iso', '')

                    try:
                        if raw_date:
                            # Use the actual Telegram message date
                            pick_time = datetime.fromisoformat(str(raw_date))
                            pick_time = pick_time.astimezone(TIMEZONE)
                            time_str = f"{pick_time.strftime('%I:%M %p')} EST {pick_time.month}/{pick_time.day}"
                        elif ts_iso:
                            # Fallback to ts_iso
                            pick_time = datetime.fromisoformat(ts_iso.replace('Z', '+00:00'))
                            pick_time = pick_time.astimezone(TIMEZONE)
                            time_str = f"{pick_time.strftime('%I:%M %p')} EST {pick_time.month}/{pick_time.day}"
                        else:
                            time_str = "??:?? EST"
                    except Exception:
                        time_str = "??:?? EST"

                    # Get pick text
                    text = pick.get('text', '').strip()

                    # Filter out unwanted text patterns from regular text
                    if text:
                        # Remove lines containing @cappersfree or DM mentions
                        text_lines = text.split('\n')
                        filtered_lines = []
                        for text_line in text_lines:
                            line_lower = text_line.lower()
                            # Skip lines with promotional content
                            if any(pattern in line_lower for pattern in [
                                '@cappersfree',
                                'dm➡️',
                                '➖➖➖➖➖',
                                'messages from ai',
                                'messages from',
                                'vip package',
                                'cheapest prices',
                                'join the best team',
                                'reach out to:',
                                'for any questions'
                            ]):
                                continue
                            filtered_lines.append(text_line)
                        text = '\n'.join(filtered_lines).strip()

                    # Initialize ocr_text for use in recap filter below
                    ocr_text = ""

                    # If no text OR very short text (just a name) but has image, try vision/OCR
                    # Short text (< 30 chars) is likely just a capper name after filtering
                    if pick.get('has_media') and pick.get('media_path') and (not text or len(text) < 30):
                        media_path = pick.get('media_path')
                        
                        # Try vision-processed data first (structured picks)
                        msg_id = pick.get('id')
                        if VISION_AVAILABLE and msg_id:
                            vision_data = get_vision_processed_picks(msg_id, 'free_cappers')
                            if vision_data and vision_data.get('picks'):
                                # Format structured picks for display
                                formatted_picks = format_structured_picks(
                                    vision_data['picks'],
                                    vision_data.get('capper_hint')
                                )
                                if formatted_picks:
                                    ocr_text = formatted_picks
                                    logger.info(f"📊 Using vision picks for msg {msg_id}")
                        
                        # Fall back to Gemini OCR if no vision data
                        if not ocr_text and os.path.exists(media_path):
                            ocr_text = extract_text_from_image(media_path)
                            if ocr_text:
                                # Also filter OCR output (in case watermarks are in image)
                                ocr_lines = ocr_text.split('\n')
                                filtered_ocr = []
                                for ocr_line in ocr_lines:
                                    line_lower = ocr_line.lower().strip()
                                    # Skip empty lines
                                    if not line_lower:
                                        continue
                                    # Skip lines with promotional content (single-line watermarks only)
                                    # Only skip if the ENTIRE line is just the watermark
                                    stripped_line = line_lower.strip()
                                    if stripped_line in ['@cappersfree', '@cappers', 'cappersfree', 'cappers', 'yourdailycapper'] or \
                                       any(pattern in stripped_line for pattern in [
                                        'dm➡️',
                                        '➖➖➖➖➖',
                                        'messages from ai',
                                        'messages from'
                                    ]):
                                        continue
                                    filtered_ocr.append(ocr_line)
                                ocr_text = '\n'.join(filtered_ocr).strip()

                                # Only add OCR text if there's actual content (not just watermarks)
                                if ocr_text and len(ocr_text) > 5:  # At least 5 chars of real content
                                    # If we have existing short text (capper name), prepend it
                                    if text:
                                        text = f"{text}\n[OCR] {ocr_text}"
                                    else:
                                        text = f"[OCR] {ocr_text}"
                                    logger.info(f"OCR extracted text from {Path(media_path).name}")

                    # Filter out recap/result messages using SMART filter
                    # Combines text + OCR and needs multiple indicators to filter
                    should_filter, filter_reason = should_filter_message(text, ocr_text)
                    if should_filter:
                        logger.info(f"Smart filtered ({filter_reason}): {text[:60]}...")
                        continue

                    # Format pick line - only add if there's meaningful text
                    if text:
                        lines.append(f"[{time_str}] {text}")
                        picks_with_content += 1

            # Update header with actual count of picks with content
            lines[header_index] = f"{emoji} {name} ({picks_with_content} picks)"
            total_picks_with_content += picks_with_content
            total_picks += pick_count

            lines.append("")

        # Footer
        lines.append("═" * 50)
        lines.append(f"Total picks today: {total_picks_with_content}")
        lines.append("")

        return "\n".join(lines)


def main():
    """Main export function"""
    logger.info("🚀 Starting Google Docs export...")

    try:
        # Initialize services
        aggregator = PicksAggregator()
        exporter = GoogleDocsExporter()

        # Load picks from sent_archive
        total_picks, channels = aggregator.load_picks()

        if total_picks == 0:
            logger.warning("⚠️ No picks found for today. Document will show empty channels.")

        # Format content
        content = aggregator.format_for_google_docs()

        # Get or create today's doc (daily rotation)
        today_str = datetime.now(TIMEZONE).strftime("%Y%m%d")
        doc_id = exporter.get_or_create_daily_doc(today_str)

        # Update Google Doc
        result_doc_id = exporter.update_document(content, doc_id)

        if result_doc_id:
            logger.info(f"✅ Export complete! {total_picks} picks from {channels} channels")
            logger.info(f"📄 View document: https://docs.google.com/document/d/{result_doc_id}/edit")
            return 0
        else:
            logger.error("❌ Export failed")
            return 1

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
