"""
Google Sheets Manager for Consensus Tracking
Handles all CRUD operations for picks, consensus, cappers, and games sheets.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import pytz

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    raise ImportError("Run: pip install gspread google-auth")

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/New_York"))

# API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Sheet column headers
PICKS_HEADERS = [
    "pick_id", "date", "time", "capper", "sport", "game", "pick", "line", 
    "odds", "units", "confidence", "result", "profit_loss", "game_id", 
    "consensus_id", "msg_id"
]

CONSENSUS_HEADERS = [
    "consensus_id", "date", "sport", "game", "side", "cappers", "strength", 
    "avg_line", "result", "alerted"
]

CAPPERS_HEADERS = [
    "capper", "total", "wins", "losses", "pushes", "win_pct", "net_units", 
    "roi", "streak", "last_pick"
]

GAMES_HEADERS = [
    "game_id", "sport", "date", "time", "away", "home", "away_score", 
    "home_score", "status"
]


class SheetsManager:
    """Manages Google Sheets operations for consensus tracking."""
    
    def __init__(self, sheet_id: str = None):
        """
        Initialize the Sheets Manager.
        
        Args:
            sheet_id: Google Sheet ID (uses env var if not provided)
        """
        self.sheet_id = sheet_id or GOOGLE_SHEET_ID
        if not self.sheet_id:
            raise ValueError("GOOGLE_SHEET_ID not set in .env or provided")
        
        self.gc = None
        self.spreadsheet = None
        self._authenticate()
        self._ensure_worksheets()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        if not GOOGLE_CREDENTIALS_PATH:
            raise ValueError("GOOGLE_CREDENTIALS_PATH not set in .env")
        
        if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
            raise FileNotFoundError(f"Credentials not found: {GOOGLE_CREDENTIALS_PATH}")
        
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH, 
            scopes=SCOPES
        )
        self.gc = gspread.authorize(creds)
        self.spreadsheet = self.gc.open_by_key(self.sheet_id)
        logger.info(f"✅ Connected to sheet: {self.spreadsheet.title}")
    
    def _ensure_worksheets(self):
        """Ensure all required worksheets exist with proper headers."""
        required_sheets = {
            "Picks": PICKS_HEADERS,
            "Consensus": CONSENSUS_HEADERS,
            "Cappers": CAPPERS_HEADERS,
            "Games": GAMES_HEADERS,
        }
        
        existing = [ws.title for ws in self.spreadsheet.worksheets()]
        
        for sheet_name, headers in required_sheets.items():
            if sheet_name not in existing:
                logger.info(f"Creating worksheet: {sheet_name}")
                ws = self.spreadsheet.add_worksheet(
                    title=sheet_name, 
                    rows=1000, 
                    cols=len(headers)
                )
                ws.append_row(headers)
            else:
                # Verify headers
                ws = self.spreadsheet.worksheet(sheet_name)
                current_headers = ws.row_values(1)
                if current_headers != headers:
                    logger.warning(f"Headers mismatch in {sheet_name}, updating...")
                    ws.update('A1', [headers])
    
    def get_worksheet(self, name: str):
        """Get a worksheet by name."""
        return self.spreadsheet.worksheet(name)
    
    # ========== PICKS OPERATIONS ==========
    
    def add_pick(self, pick: Dict[str, Any]) -> bool:
        """
        Add a single pick to the Picks sheet.
        
        Args:
            pick: Dictionary with pick data matching PICKS_HEADERS
        
        Returns:
            True if successful
        """
        ws = self.get_worksheet("Picks")
        
        row = [
            pick.get("pick_id", ""),
            pick.get("date", ""),
            pick.get("time", ""),
            pick.get("capper", ""),
            pick.get("sport", ""),
            pick.get("game", ""),
            pick.get("pick", ""),
            pick.get("line", ""),
            pick.get("odds", ""),
            pick.get("units", ""),
            pick.get("confidence", ""),
            pick.get("result", ""),
            pick.get("profit_loss", ""),
            pick.get("game_id", ""),
            pick.get("consensus_id", ""),
            pick.get("msg_id", ""),
        ]
        
        ws.append_row(row, value_input_option='USER_ENTERED')
        logger.debug(f"Added pick: {pick.get('pick_id')}")
        return True
    
    def add_picks_batch(self, picks: List[Dict[str, Any]]) -> int:
        """
        Add multiple picks in a batch (more efficient).
        
        Args:
            picks: List of pick dictionaries
        
        Returns:
            Number of picks added
        """
        if not picks:
            return 0
        
        ws = self.get_worksheet("Picks")
        
        rows = []
        for pick in picks:
            row = [
                pick.get("pick_id", ""),
                pick.get("date", ""),
                pick.get("time", ""),
                pick.get("capper", ""),
                pick.get("sport", ""),
                pick.get("game", ""),
                pick.get("pick", ""),
                pick.get("line", ""),
                pick.get("odds", ""),
                pick.get("units", ""),
                pick.get("confidence", ""),
                pick.get("result", ""),
                pick.get("profit_loss", ""),
                pick.get("game_id", ""),
                pick.get("consensus_id", ""),
                pick.get("msg_id", ""),
            ]
            rows.append(row)
        
        ws.append_rows(rows, value_input_option='USER_ENTERED')
        logger.info(f"Added {len(rows)} picks to sheet")
        return len(rows)
    
    def get_picks_by_date(self, date_str: str) -> List[Dict]:
        """Get all picks for a specific date."""
        ws = self.get_worksheet("Picks")
        all_data = ws.get_all_records()
        return [p for p in all_data if p.get("date") == date_str]
    
    def get_pick_by_msg_id(self, msg_id: int) -> Optional[Dict]:
        """Check if a pick already exists by message ID."""
        ws = self.get_worksheet("Picks")
        all_data = ws.get_all_records()
        for pick in all_data:
            if str(pick.get("msg_id")) == str(msg_id):
                return pick
        return None
    
    def update_pick_result(self, pick_id: str, result: str, profit_loss: float = None):
        """Update the result of a pick."""
        ws = self.get_worksheet("Picks")
        
        # Find the row with this pick_id
        cell = ws.find(pick_id)
        if cell:
            row = cell.row
            # Result is column L (12), profit_loss is column M (13)
            ws.update_cell(row, 12, result)
            if profit_loss is not None:
                ws.update_cell(row, 13, profit_loss)
            logger.info(f"Updated pick {pick_id}: {result}")
            return True
        return False
    
    # ========== CONSENSUS OPERATIONS ==========
    
    def add_consensus(self, consensus: Dict[str, Any]) -> bool:
        """Add a consensus record."""
        ws = self.get_worksheet("Consensus")
        
        # Convert list of cappers to comma-separated string
        cappers = consensus.get("cappers", [])
        if isinstance(cappers, list):
            cappers = ", ".join(cappers)
        
        row = [
            consensus.get("consensus_id", ""),
            consensus.get("date", ""),
            consensus.get("sport", ""),
            consensus.get("game", ""),
            consensus.get("side", ""),
            cappers,
            consensus.get("strength", ""),
            consensus.get("avg_line", ""),
            consensus.get("result", ""),
            consensus.get("alerted", False),
        ]
        
        ws.append_row(row, value_input_option='USER_ENTERED')
        logger.info(f"Added consensus: {consensus.get('consensus_id')}")
        return True
    
    def get_consensus_by_date(self, date_str: str) -> List[Dict]:
        """Get all consensus records for a date."""
        ws = self.get_worksheet("Consensus")
        all_data = ws.get_all_records()
        return [c for c in all_data if c.get("date") == date_str]
    
    def get_consensus_by_id(self, consensus_id: str) -> Optional[Dict]:
        """Get a specific consensus record."""
        ws = self.get_worksheet("Consensus")
        all_data = ws.get_all_records()
        for c in all_data:
            if c.get("consensus_id") == consensus_id:
                return c
        return None
    
    def update_consensus_result(self, consensus_id: str, result: str):
        """Update the result of a consensus pick."""
        ws = self.get_worksheet("Consensus")
        cell = ws.find(consensus_id)
        if cell:
            row = cell.row
            # Result is column I (9)
            ws.update_cell(row, 9, result)
            logger.info(f"Updated consensus {consensus_id}: {result}")
            return True
        return False
    
    def mark_consensus_alerted(self, consensus_id: str):
        """Mark a consensus as having been alerted."""
        ws = self.get_worksheet("Consensus")
        cell = ws.find(consensus_id)
        if cell:
            row = cell.row
            # Alerted is column J (10)
            ws.update_cell(row, 10, True)
            return True
        return False
    
    # ========== CAPPERS OPERATIONS ==========
    
    def update_capper_stats(self, capper: str, stats: Dict[str, Any]):
        """Update or create capper stats."""
        ws = self.get_worksheet("Cappers")
        
        row = [
            capper,
            stats.get("total", 0),
            stats.get("wins", 0),
            stats.get("losses", 0),
            stats.get("pushes", 0),
            stats.get("win_pct", "0%"),
            stats.get("net_units", 0),
            stats.get("roi", "0%"),
            stats.get("streak", ""),
            stats.get("last_pick", ""),
        ]
        
        # Check if capper exists
        try:
            cell = ws.find(capper)
            if cell:
                # Update existing row
                ws.update(f'A{cell.row}:J{cell.row}', [row])
                logger.debug(f"Updated capper stats: {capper}")
            else:
                raise gspread.exceptions.CellNotFound
        except gspread.exceptions.CellNotFound:
            # Add new row
            ws.append_row(row, value_input_option='USER_ENTERED')
            logger.debug(f"Added new capper: {capper}")
    
    def get_capper_stats(self, capper: str) -> Optional[Dict]:
        """Get stats for a specific capper."""
        ws = self.get_worksheet("Cappers")
        all_data = ws.get_all_records()
        for c in all_data:
            if c.get("capper") == capper:
                return c
        return None
    
    def get_all_capper_stats(self) -> List[Dict]:
        """Get stats for all cappers."""
        ws = self.get_worksheet("Cappers")
        return ws.get_all_records()
    
    # ========== GAMES OPERATIONS ==========
    
    def add_game(self, game: Dict[str, Any]) -> bool:
        """Add a game record."""
        ws = self.get_worksheet("Games")
        
        row = [
            game.get("game_id", ""),
            game.get("sport", ""),
            game.get("date", ""),
            game.get("time", ""),
            game.get("away", ""),
            game.get("home", ""),
            game.get("away_score", ""),
            game.get("home_score", ""),
            game.get("status", "scheduled"),
        ]
        
        ws.append_row(row, value_input_option='USER_ENTERED')
        return True
    
    def get_game_by_id(self, game_id: str) -> Optional[Dict]:
        """Get a game by ID."""
        ws = self.get_worksheet("Games")
        all_data = ws.get_all_records()
        for g in all_data:
            if g.get("game_id") == game_id:
                return g
        return None
    
    def update_game_score(self, game_id: str, away_score: int, home_score: int, status: str = "final"):
        """Update game scores."""
        ws = self.get_worksheet("Games")
        cell = ws.find(game_id)
        if cell:
            row = cell.row
            # away_score is G (7), home_score is H (8), status is I (9)
            ws.update_cell(row, 7, away_score)
            ws.update_cell(row, 8, home_score)
            ws.update_cell(row, 9, status)
            logger.info(f"Updated game {game_id}: {away_score}-{home_score}")
            return True
        return False
    
    # ========== UTILITY METHODS ==========
    
    def clear_sheet(self, sheet_name: str, keep_headers: bool = True):
        """Clear all data from a sheet."""
        ws = self.get_worksheet(sheet_name)
        if keep_headers:
            # Keep first row, clear rest
            if ws.row_count > 1:
                ws.delete_rows(2, ws.row_count)
        else:
            ws.clear()
        logger.info(f"Cleared sheet: {sheet_name}")
    
    def get_sheet_url(self) -> str:
        """Get the URL of the spreadsheet."""
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit"


# Singleton instance for convenience
_manager_instance = None

def get_sheets_manager() -> SheetsManager:
    """Get or create the SheetsManager singleton."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SheetsManager()
    return _manager_instance
