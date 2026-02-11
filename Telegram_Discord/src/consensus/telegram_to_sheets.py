#!/usr/bin/env python3
"""
Telegram to Sheets Exporter
Exports picks from Telegram free_cappers to the AllPicks sheet.

Matches the existing format: Site | League | Date | Matchup | Service | Pick | RunDate
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import pytz

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import gspread
from google.oauth2.service_account import Credentials

# Try to import vision processor for structured picks
try:
    from src.utils.vision_formatter import get_vision_processed_picks
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

# Import OCR from existing gdocs exporter
try:
    from src.export_to_gdocs import extract_text_from_image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from src.utils.smart_recap_filter import should_filter_message

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone("America/New_York")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1dZe1s-yLHYvrLQEAlP0gGCVAFNbH433lV82iHzp-_BI")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

BASE_DIR = Path(__file__).parent.parent.parent
SENT_ARCHIVE_DIR = BASE_DIR / "sent_archive"
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(exist_ok=True)

PROCESSED_STATE_FILE = STATE_DIR / "telegram_to_sheets_processed.json"

# Channels to export (map folder name to display name)
CHANNELS = {
    "free_cappers": "TG-FreeCapper",
    "exclusive_cappers": "TG-Exclusive",
    "new_free_channel": "TG-NewFree",
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def load_processed_ids() -> Set[str]:
    """Load already-processed message IDs."""
    if PROCESSED_STATE_FILE.exists():
        try:
            with open(PROCESSED_STATE_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except Exception:
            pass
    return set()


def save_processed_ids(ids: Set[str]):
    """Save processed message IDs."""
    ids_list = list(ids)
    # Keep last 10K to avoid bloat
    if len(ids_list) > 10000:
        ids_list = ids_list[-10000:]
    with open(PROCESSED_STATE_FILE, 'w') as f:
        json.dump({
            "processed_ids": ids_list,
            "last_updated": datetime.now(TIMEZONE).isoformat()
        }, f, indent=2)


class TelegramToSheetsExporter:
    """Exports Telegram picks to AllPicks sheet."""
    
    def __init__(self, date_str: str = None):
        self.date_str = date_str or datetime.now(TIMEZONE).strftime("%Y%m%d")
        self.date_formatted = datetime.strptime(self.date_str, "%Y%m%d").strftime("%Y-%m-%d")
        
        self.gc = None
        self.spreadsheet = None
        self._authenticate()
        
        self.processed_ids = load_processed_ids()
        self.new_ids = set()
        
        self.picks_added = 0
        self.duplicates_skipped = 0
    
    def _authenticate(self):
        """Authenticate with Google Sheets."""
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=SCOPES
        )
        self.gc = gspread.authorize(creds)
        self.spreadsheet = self.gc.open_by_key(SHEET_ID)
        logger.info(f"Connected to: {self.spreadsheet.title}")
    
    def load_telegram_picks(self) -> List[Dict]:
        """Load picks from Telegram sent_archive for today."""
        all_picks = []
        archive_path = SENT_ARCHIVE_DIR / self.date_str
        
        if not archive_path.exists():
            logger.warning(f"No archive found for {self.date_str}")
            return []
        
        for channel_folder, site_name in CHANNELS.items():
            channel_path = archive_path / channel_folder
            if not channel_path.exists():
                continue
            
            for json_file in channel_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    msg_id = str(data.get('id', ''))
                    
                    # Skip if already processed
                    if msg_id in self.processed_ids:
                        self.duplicates_skipped += 1
                        continue
                    
                    # Add site info
                    data['_site'] = site_name
                    data['_channel'] = channel_folder
                    all_picks.append(data)
                    
                except Exception as e:
                    logger.error(f"Error reading {json_file}: {e}")
        
        logger.info(f"Loaded {len(all_picks)} new picks from Telegram")
        return all_picks
    
    def _extract_capper_from_text(self, text: str) -> str:
        """Extract capper name from Telegram message text."""
        if not text:
            return "Unknown"
        
        import re
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        if not lines:
            return "Unknown"
        
        # Bad capper names to skip (lowercase)
        bad_names = ['exclusive play', 'main play', 'vip', 'free picks', 'dm', 
                     'cappers free', 'owner', 'price', 'cheapest', 'play', 
                     'today', 'card', 'picks', 'tuesday', 'wednesday', 'thursday',
                     'friday', 'saturday', 'sunday', 'monday', 'premium', 'exclusive']
        
        # Clean first line - strip punctuation from end
        first_line = lines[0].strip().rstrip('.').rstrip(',').strip()
        first_lower = first_line.lower()
        
        # Skip if empty after cleaning
        if not first_line:
            pass
        # Skip if it's a bad/generic name
        elif any(bad == first_lower or first_lower.startswith(bad + ' ') for bad in bad_names):
            pass
        # Skip if it looks like a pick (has +/- numbers, but allow "a11bets" style names)
        elif re.search(r'[+-]\s*\d+\.?\d*', first_line):
            pass
        # Skip if too long (probably not a name)
        elif len(first_line) > 35:
            pass
        # Skip if it's mostly emoji/punctuation (less than 2 alphanumeric chars)
        elif len(re.sub(r'[^\w]', '', first_line)) < 2:
            pass
        # Skip if it starts with a number (unless it's like "25Legs")
        elif first_line[0].isdigit() and not any(c.isalpha() for c in first_line[:3]):
            pass
        else:
            # Looks like a capper name!
            return first_line
        
        # Check for pattern: "Name\npicks..." where name is on its own line
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            line_clean = line.strip().rstrip('.').rstrip(',').strip()
            line_lower = line_clean.lower()
            
            # Skip bad names
            if any(bad == line_lower or line_lower.startswith(bad + ' ') for bad in bad_names):
                continue
            # Skip picks
            if re.search(r'[+-]\s*\d+\.?\d*', line_clean):
                continue
            # Skip too long/short
            if len(line_clean) > 35 or len(line_clean) < 2:
                continue
            # Skip mostly emoji
            if len(re.sub(r'[^\w]', '', line_clean)) < 2:
                continue
            # Skip sport headers
            if line_lower in ['nba', 'nfl', 'nhl', 'mlb', 'ncaab', 'ncaaf', 'tennis', 'soccer', 'euroleague', 'cbb', 'cfb']:
                continue
                
            # If next line has picks or sport, this line is likely the capper
            if i < len(lines) - 1:
                next_line = lines[i + 1].lower()
                if re.search(r'[+-]\d+|ml\b|over|under|spread|parlay|\du\b', next_line, re.I):
                    return line_clean
                if any(sport in next_line for sport in ['nba', 'nfl', 'nhl', 'ncaab', 'cbb', 'tennis']):
                    return line_clean
        
        return "Unknown"
    
    def extract_picks_from_message(self, msg: Dict) -> List[Dict]:
        """
        Extract structured picks from a message.
        Returns list of picks in AllPicks format.
        """
        msg_id = msg.get('id', '')
        text = msg.get('text', '').strip()
        has_media = msg.get('has_media', False)
        media_path = msg.get('media_path', '')
        channel = msg.get('_channel', 'free_cappers')
        site = msg.get('_site', 'TG-FreeCapper')
        
        # Extract capper from message text
        capper_from_text = self._extract_capper_from_text(text)
        
        picks = []
        ocr_text = ""
        
        # Try vision-processed data for images
        if has_media and VISION_AVAILABLE:
            vision_data = get_vision_processed_picks(msg_id, channel)
            if vision_data and vision_data.get('picks'):
                for vp in vision_data['picks']:
                    # Use extracted capper, or vision capper, or fallback
                    service = vp.get('capper') or capper_from_text or vision_data.get('capper_hint') or 'Unknown'
                    pick = self._format_pick(
                        site=site,
                        league=vp.get('sport', ''),
                        matchup=vp.get('game', ''),
                        service=service,
                        pick_text=vp.get('pick', ''),
                        date=self.date_formatted
                    )
                    if pick:
                        picks.append(pick)
        
        # If no vision data but has image, try OCR
        if not picks and has_media and media_path and OCR_AVAILABLE:
            if os.path.exists(media_path):
                ocr_text = extract_text_from_image(media_path)
                if ocr_text and "[RESULT_SCREENSHOT]" not in ocr_text:
                    # Parse OCR text - use extracted capper name
                    capper_hint = capper_from_text if capper_from_text != "Unknown" else text
                    parsed = self._parse_ocr_text(ocr_text, site, capper_hint)
                    picks.extend(parsed)
        
        # Try parsing plain text if no picks yet
        if not picks and text and len(text) > 10:
            # Filter out recaps
            should_filter, reason = should_filter_message(text, ocr_text)
            if should_filter:
                logger.debug(f"Filtered: {reason}")
                return []
            
            # Basic text parsing - pass extracted capper
            parsed = self._parse_text_message(text, site, capper_from_text)
            picks.extend(parsed)
        
        return picks
    
    def _parse_ocr_text(self, ocr_text: str, site: str, capper: str) -> List[Dict]:
        """Parse OCR-extracted text into picks."""
        picks = []
        lines = ocr_text.split('\n')
        
        current_sport = ""
        # Clean up capper name from the start
        detected_capper = capper.strip().rstrip(',').strip() if capper else "Unknown"
        
        # Sport detection
        sport_keywords = {
            "NBA": ["nba", "basketball"],
            "NFL": ["nfl", "football"],
            "NCAAB": ["ncaab", "college basketball", "cbb", "ncaa basketball", "college hoops"],
            "NHL": ["nhl", "hockey"],
            "MLB": ["mlb", "baseball"],
            "SOCCER": ["soccer", "epl", "ucl", "premier league"],
            "TENNIS": ["tennis", "atp", "wta"],
            "EUROLEAGUE": ["euroleague", "euro league"],
        }
        
        import re
        
        for line in lines:
            # Clean up line - remove bullets and extra whitespace
            line = line.strip()
            line = re.sub(r'^[•\-\*]\s*', '', line)  # Remove bullet points
            line = line.strip()
            
            if not line or len(line) < 3:
                continue
            
            line_lower = line.lower()
            
            # Skip promotional/watermark lines
            skip_patterns = ['@cappers', 'dm me', 'vip', 'messages from', 'package', 'subscribe']
            if any(p in line_lower for p in skip_patterns):
                continue
            
            # Check if line is just a capper name (short, no numbers)
            if len(line) < 25 and not re.search(r'\d', line) and not any(kw in line_lower for kws in sport_keywords.values() for kw in kws):
                # Could be capper name - clean it up
                if line and not line.endswith(':'):
                    detected_capper = line.strip().rstrip(',').strip()
                continue
            
            # Detect sport header
            for sport, keywords in sport_keywords.items():
                if any(kw in line_lower for kw in keywords):
                    if ':' in line or len(line) < 30:  # Likely a header
                        current_sport = sport
                        continue
            
            # Look for pick patterns - more flexible matching
            pick_patterns = [
                # Team @ Team: Over/Under X
                r'(.+?@.+?):\s*(over|under)\s*(\d+\.?\d*)',
                # Team +/- spread
                r'([A-Za-z][A-Za-z\s\-\.]+?)\s*([+-]\d+\.?\d*)',
                # Team ML
                r'([A-Za-z][A-Za-z\s\-\.]+?)\s+(ML|ml|Ml)',
                # Over/Under X
                r'(over|under)\s*(\d+\.?\d*)',
                # Player prop: Name Over/Under X
                r'([A-Za-z][A-Za-z\s]+?)\s+(over|under)\s*(\d+\.?\d*)',
                # Just has odds like -110, -125
                r'(.+?)\s+(-?\d{3})\s*$',
            ]
            
            matched = False
            for pattern in pick_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Clean up the pick text
                    pick_text = line
                    # Remove unit info like "1U", "2 units"
                    pick_text = re.sub(r'\s+\d+\.?\d*\s*[Uu](nits?)?', '', pick_text)
                    pick_text = pick_text.strip()
                    
                    pick = self._format_pick(
                        site=site,
                        league=current_sport,
                        matchup="",
                        service=detected_capper,
                        pick_text=pick_text,
                        date=self.date_formatted
                    )
                    if pick:
                        picks.append(pick)
                    matched = True
                    break
            
            # If no pattern matched but line looks like a pick (has odds/numbers)
            if not matched and re.search(r'[+-]?\d{2,}', line) and len(line) > 10:
                pick = self._format_pick(
                    site=site,
                    league=current_sport,
                    matchup="",
                    service=detected_capper,
                    pick_text=line,
                    date=self.date_formatted
                )
                if pick:
                    picks.append(pick)
        
        return picks
    
    def _format_pick(self, site: str, league: str, matchup: str, 
                     service: str, pick_text: str, date: str) -> Dict:
        """Format a pick for AllPicks sheet."""
        if not pick_text or len(pick_text) < 3:
            return None
        
        # Clean up service name - strip whitespace and trailing commas
        clean_service = service.strip().rstrip(',').strip() if service else "Unknown"
        
        # Try to extract matchup from pick_text if matchup is empty
        # Look for patterns like "Team @ Team" or "Team vs Team"
        clean_matchup = matchup.strip() if matchup else ""
        if not clean_matchup:
            import re
            # Pattern: Team @ Team or Team vs Team
            matchup_match = re.search(r'([A-Za-z][A-Za-z\s\.\-]+?)\s*(?:@|vs\.?|v\.?)\s*([A-Za-z][A-Za-z\s\.\-]+?)(?:\s*[:\-]|\s*$)', pick_text, re.IGNORECASE)
            if matchup_match:
                away = matchup_match.group(1).strip()
                home = matchup_match.group(2).strip()
                # Clean up - remove common suffixes that aren't team names
                for suffix in ['over', 'under', 'ml', 'pk']:
                    if away.lower().endswith(suffix):
                        away = away[:-len(suffix)].strip()
                    if home.lower().endswith(suffix):
                        home = home[:-len(suffix)].strip()
                if away and home and len(away) > 2 and len(home) > 2:
                    clean_matchup = f"{away} @ {home}"
        
        # Ensure date is in ISO format string (YYYY-MM-DD)
        # Using RAW input in write_to_allpicks prevents Excel serial conversion
        clean_date = date if date else ""
        
        return {
            "Site": site,
            "League": league.upper() if league else "",
            "Date": clean_date,
            "Matchup": clean_matchup,
            "Service": clean_service,
            "Pick": pick_text.strip(),
            "RunDate": clean_date,
        }
    
    def _parse_text_message(self, text: str, site: str, default_capper: str = "Unknown") -> List[Dict]:
        """Parse a text message into picks."""
        picks = []
        lines = text.split('\n')
        
        current_sport = ""
        # Use extracted capper as default
        current_capper = default_capper if default_capper != "Unknown" else ""
        
        # Sport keywords
        sport_keywords = {
            "NBA": ["nba", "basketball"],
            "NFL": ["nfl", "football"],
            "NCAAB": ["ncaab", "college basketball", "cbb", "ncaa basketball"],
            "NCAAF": ["ncaaf", "college football", "cfb"],
            "NHL": ["nhl", "hockey"],
            "MLB": ["mlb", "baseball"],
            "SOCCER": ["soccer", "epl", "la liga", "ucl", "mls"],
            "TENNIS": ["tennis", "atp", "wta"],
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            # Check for sport header
            for sport, keywords in sport_keywords.items():
                if any(kw in line_lower for kw in keywords):
                    current_sport = sport
                    break
            
            # Check for capper name (often first non-empty line or has "picks" in it)
            if "pick" in line_lower and len(line) < 50:
                current_capper = line.split()[0] if line.split() else ""
                continue
            
            # Look for pick patterns: team +/- number, ML, over/under
            import re
            pick_patterns = [
                r'([A-Za-z\s]+)\s*([+-]\d+\.?\d*)',  # Team +/- spread
                r'([A-Za-z\s]+)\s+(ML|ml|Ml)',       # Team ML
                r'(Over|Under|OVER|UNDER)\s*(\d+\.?\d*)',  # Total
            ]
            
            for pattern in pick_patterns:
                match = re.search(pattern, line)
                if match:
                    # Use current_capper (extracted from text) or default_capper
                    service = current_capper if current_capper else default_capper
                    if not service or service == "Unknown":
                        service = "Unknown"
                    pick = self._format_pick(
                        site=site,
                        league=current_sport,
                        matchup="",  # Would need more parsing
                        service=service,
                        pick_text=line,
                        date=self.date_formatted
                    )
                    if pick:
                        picks.append(pick)
                    break
        
        return picks
    
    def write_to_allpicks(self, picks: List[Dict]) -> int:
        """Write picks to AllPicks sheet."""
        if not picks:
            return 0
        
        ws = self.spreadsheet.worksheet("AllPicks")
        
        # Find the last row with actual data in column A
        col_a = ws.col_values(1)  # Get all values in column A
        last_row = len([v for v in col_a if v.strip()])  # Count non-empty
        
        rows = []
        for p in picks:
            # Validate required fields before adding
            site = p.get("Site", "").strip()
            pick_text = p.get("Pick", "").strip()
            
            # Skip picks without essential data
            if not pick_text:
                logger.debug(f"Skipping pick with empty Pick field")
                continue
            
            # Ensure exactly 7 columns (Site through RunDate) - no extras
            row = [
                site if site else "TG-Unknown",  # Site - never empty
                p.get("League", "").strip(),      # League
                p.get("Date", "").strip(),        # Date - ISO format (YYYY-MM-DD)
                p.get("Matchup", "").strip(),     # Matchup
                p.get("Service", "").strip().rstrip(','),  # Service - strip trailing commas
                pick_text,                         # Pick
                p.get("RunDate", "").strip(),     # RunDate - ISO format
            ]
            rows.append(row)
        
        if not rows:
            logger.warning("No valid picks to write after validation")
            return 0
        
        # Insert at specific row range (after last data row)
        start_row = last_row + 1
        end_row = start_row + len(rows) - 1
        cell_range = f'A{start_row}:G{end_row}'
        
        # Use RAW to prevent date conversion to Excel serial numbers
        ws.update(cell_range, rows, value_input_option='RAW')
        logger.info(f"Added {len(rows)} picks to AllPicks (rows {start_row}-{end_row})")
        
        return len(rows)
    
    def run(self) -> Dict:
        """Run the full export pipeline."""
        logger.info(f"Exporting Telegram picks for {self.date_formatted}")
        
        # Load picks
        messages = self.load_telegram_picks()
        
        if not messages:
            return {
                "date": self.date_formatted,
                "messages": 0,
                "picks": 0,
                "duplicates": self.duplicates_skipped
            }
        
        # Extract structured picks
        all_picks = []
        for msg in messages:
            picks = self.extract_picks_from_message(msg)
            all_picks.extend(picks)
            
            # Mark as processed
            msg_id = str(msg.get('id', ''))
            if msg_id:
                self.new_ids.add(msg_id)
        
        # Write to sheet
        written = self.write_to_allpicks(all_picks)
        self.picks_added = written
        
        # Save processed IDs
        self.processed_ids.update(self.new_ids)
        save_processed_ids(self.processed_ids)
        
        return {
            "date": self.date_formatted,
            "messages": len(messages),
            "picks": written,
            "duplicates": self.duplicates_skipped,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Export Telegram picks to Google Sheets")
    parser.add_argument("--date", help="Date in YYYYMMDD format (default: today)")
    args = parser.parse_args()
    
    try:
        exporter = TelegramToSheetsExporter(date_str=args.date)
        stats = exporter.run()
        
        print(f"\n{'='*50}")
        print(f"Telegram to Sheets Export - {stats['date']}")
        print(f"{'='*50}")
        print(f"Messages processed: {stats['messages']}")
        print(f"Picks added:        {stats['picks']}")
        print(f"Duplicates skipped: {stats['duplicates']}")
        print(f"\nSheet: {stats.get('sheet_url', '')}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
