#!/usr/bin/env python3
"""
Consensus Scanner
Scans the AllPicks sheet for consensus plays and writes to Consensus tab.

Reads existing format: Site | League | Date | Matchup | Service | Pick | RunDate
Groups by Matchup + Pick side to find 2+ sources on same side.
"""

import os
import sys
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import hashlib
import pytz

sys.path.insert(0, str(__file__).rsplit('src', 1)[0])

from dotenv import load_dotenv
load_dotenv()

import gspread
from google.oauth2.service_account import Credentials

from src.consensus.team_mappings import normalize_team

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone("America/New_York")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
if not SHEET_ID:
    raise ValueError("GOOGLE_SHEET_ID environment variable is required")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


class ConsensusScanner:
    """Scans AllPicks for consensus and writes to Consensus tab."""
    
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets."""
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=SCOPES
        )
        self.gc = gspread.authorize(creds)
        self.spreadsheet = self.gc.open_by_key(SHEET_ID)
        logger.info(f"Connected to: {self.spreadsheet.title}")
    
    def get_picks_for_date(self, date_str: str = None) -> List[Dict]:
        """
        Get all picks for a specific date from AllPicks.
        
        Args:
            date_str: Date in YYYY-MM-DD format (default: today)
        
        Returns:
            List of pick dictionaries
        """
        if date_str is None:
            date_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
        
        ws = self.spreadsheet.worksheet("AllPicks")
        
        # Get all values as lists (more robust than get_all_records for messy data)
        all_values = ws.get_all_values()
        
        if not all_values:
            return []
        
        # Use first row as headers
        headers = all_values[0]
        
        # Clean up headers - remove empty ones, handle duplicates
        clean_headers = []
        for i, h in enumerate(headers):
            if h:
                clean_headers.append(h)
            else:
                clean_headers.append(f"col_{i}")
        
        # Convert to list of dicts
        picks = []
        for row in all_values[1:]:
            # Create dict from row
            row_dict = {}
            for i, val in enumerate(row):
                if i < len(clean_headers):
                    row_dict[clean_headers[i]] = val
            
            # Filter by date
            row_date = row_dict.get("Date", "")
            if date_str in str(row_date) or str(row_date) == date_str:
                picks.append(row_dict)
        
        logger.info(f"Found {len(picks)} picks for {date_str}")
        return picks
    
    def normalize_pick(self, pick_text: str) -> Tuple[str, float, str]:
        """
        Normalize a pick string into (team, line, pick_type).
        
        Examples:
            "Bulls -5.5" -> ("CHI", -5.5, "spread")
            "Lakers ML" -> ("LAL", None, "ml")
            "Over 220.5" -> ("OVER", 220.5, "total")
            "Seattle @ New England: Under 46.5" -> ("UNDER", 46.5, "total")
            "Bills +180" -> ("BUF", None, "ml")  # 3-digit = ML odds, not spread
        """
        if not pick_text:
            return ("", None, "unknown")
        
        text = pick_text.strip()
        text_lower = text.lower()
        
        # Handle totals (Over/Under) - check anywhere in string
        if "over" in text_lower or "under" in text_lower:
            direction = "OVER" if "over" in text_lower else "UNDER"
            match = re.search(r'(\d+\.?\d*)', text)
            line = float(match.group(1)) if match else None
            return (direction, line, "total")
        
        # Handle explicit moneyline
        if "ml" in text_lower or "moneyline" in text_lower:
            # Extract team name (everything before ML)
            team_part = re.sub(r'\s*(ml|moneyline).*', '', text, flags=re.I).strip()
            # Also remove odds like -110
            team_part = re.sub(r'\s*[+-]?\d{3}\s*$', '', team_part).strip()
            team_code, _ = normalize_team(team_part)
            return (team_code, None, "ml")
        
        # Handle spread FIRST (team +/- number with 1-2 digits before decimal)
        # Valid spreads: -5.5, +3, -10.5, +14
        # NOT valid spreads: -110, +180 (these are odds)
        # Pattern matches: "Team -5.5", "Team -3.5 (-110)", etc.
        spread_match = re.search(r'(.+?)\s*([+-]\d{1,2}(?:\.\d+)?)\s*(?:\(|$|[^\d]|$)', text)
        if spread_match:
            team_part = spread_match.group(1).strip()
            line_str = spread_match.group(2)
            line = float(line_str)
            
            # Double-check: spreads are typically -50 to +50
            # If the number is outside this range, skip and check for ML
            if abs(line) <= 50:
                team_code, _ = normalize_team(team_part)
                return (team_code, line, "spread")
        
        # Check for 3-digit numbers (these are ML ODDS, not spreads!)
        # Pattern: Team +180, Team -150, etc.
        ml_odds_match = re.search(r'(.+?)\s*([+-]\d{3,})\s*', text)
        if ml_odds_match:
            team_part = ml_odds_match.group(1).strip()
            # Remove any parenthetical or trailing text
            team_part = re.sub(r'\s*\(.*?\)', '', team_part).strip()
            team_code, _ = normalize_team(team_part)
            # This is ML, the number is odds not a line
            return (team_code, None, "ml")
        
        # Just a team name (treat as ML)
        team_code, _ = normalize_team(text)
        return (team_code, None, "ml")
    
    def normalize_matchup(self, matchup: str) -> str:
        """
        Normalize a matchup string for grouping.
        
        Examples:
            "Bulls vs Pistons" -> "CHI@DET"
            "LAL @ BOS" -> "LAL@BOS"
            "SEA@New England:" -> "SEA@NE"
        """
        if not matchup:
            return ""
        
        # Skip "Unknown" matchups
        if matchup.strip().lower() == "unknown":
            return ""
        
        # Clean up trailing punctuation
        matchup = matchup.strip().rstrip(':').strip()
        
        # Split on common separators
        separators = [" @ ", " at ", " vs ", " vs. ", " v ", " - ", "@"]
        teams = []
        
        for sep in separators:
            if sep.lower() in matchup.lower():
                parts = re.split(re.escape(sep), matchup, flags=re.I)
                if len(parts) == 2:
                    teams = [p.strip() for p in parts]
                    break
        
        if len(teams) != 2:
            # Can't parse as matchup, return cleaned version
            code, _ = normalize_team(matchup)
            return code if code else matchup.upper()
        
        # Clean team names of trailing punctuation
        teams = [t.rstrip(':').strip() for t in teams]
        
        away_code, _ = normalize_team(teams[0])
        home_code, _ = normalize_team(teams[1])
        
        return f"{away_code}@{home_code}"
    
    def clean_source(self, source: str) -> str:
        """
        Clean a source name - remove commas, strip whitespace, handle empty.
        """
        if not source:
            return ""
        # Remove leading/trailing whitespace and commas
        cleaned = source.strip().strip(',').strip()
        # Skip "Unknown" as a source
        if cleaned.lower() == "unknown":
            return ""
        return cleaned
    
    def extract_matchup_from_pick(self, pick_text: str, league: str = "") -> str:
        """
        Try to extract matchup from the pick text when Matchup field is empty.
        
        Looks for patterns like:
        - "Team1/Team2 over 220" -> "Team1@Team2"
        - "Team1 vs Team2: Under 45" -> "Team1@Team2"
        - "Team1 @ Team2" -> "Team1@Team2"
        """
        if not pick_text:
            return ""
        
        # Pattern: "Team1/Team2" (common for totals)
        # Stop at over/under/numbers
        slash_match = re.search(r'^([A-Za-z\s]+)/([A-Za-z\s]+?)(?:\s+(?:over|under|o|u|\d)|$)', pick_text, re.I)
        if slash_match:
            team1, team2 = slash_match.group(1).strip(), slash_match.group(2).strip()
            code1, _ = normalize_team(team1)
            code2, _ = normalize_team(team2)
            return f"{code1}@{code2}"
        
        # Pattern: "Team vs Team" or "Team @ Team"
        # Stop at colon, over/under, or numbers
        vs_match = re.search(r'([A-Za-z\s]+)\s*(?:vs\.?|@|at)\s*([A-Za-z\s]+?)(?:\s*[:;]|\s+(?:over|under|o|u|\d)|$)', pick_text, re.I)
        if vs_match:
            team1, team2 = vs_match.group(1).strip(), vs_match.group(2).strip()
            # Clean off trailing punctuation or numbers
            team1 = re.sub(r'[\d:]+.*$', '', team1).strip()
            team2 = re.sub(r'[\d:]+.*$', '', team2).strip()
            code1, _ = normalize_team(team1)
            code2, _ = normalize_team(team2)
            return f"{code1}@{code2}"
        
        return ""
    
    def detect_consensus(self, picks: List[Dict], min_sources: int = 2) -> List[Dict]:
        """
        Detect consensus plays from picks.
        
        Groups picks by matchup + pick side, finds where 2+ sources agree.
        """
        # Group by normalized pick (more flexible matching)
        groups = defaultdict(list)
        
        for pick in picks:
            matchup = self.normalize_matchup(pick.get("Matchup", ""))
            pick_text = pick.get("Pick", "")
            team, line, pick_type = self.normalize_pick(pick_text)
            league = pick.get("League", "").upper()
            
            # Try multiple ways to get matchup if empty
            if not matchup or matchup == "UNKNOWN":
                # Try extracting from pick text
                matchup = self.extract_matchup_from_pick(pick_text, league)
            
            # Try to get matchup from team context (if we know the team)
            if not matchup and team and team not in ("OVER", "UNDER"):
                # Use team as partial matchup (better than nothing)
                matchup = team
            
            if not team:
                continue
            
            # Clean source name
            source = self.clean_source(pick.get("Service", ""))
            if not source:
                source = self.clean_source(pick.get("Site", ""))
            if not source:
                # Skip picks with no valid source
                continue
            
            # Create group key - be flexible about matchup
            # For totals, key on OVER/UNDER + approximate line
            if pick_type == "total":
                line_group = int(line) if line else 0  # Group by whole number
                key = f"{team}_{line_group}"
            elif pick_type == "spread":
                # Group spreads by team + direction (fav/dog)
                direction = "fav" if line and line < 0 else "dog"
                key = f"{team}_{direction}_{pick_type}"  # Add pick_type to key
            else:
                # ML - just by team
                key = f"{team}_ML"
            
            # Add sport/league prefix for better grouping
            if league:
                key = f"{league}_{key}"
            
            groups[key].append({
                "source": source,
                "pick": pick_text,
                "team": team,
                "line": line,
                "pick_type": pick_type,
                "matchup": matchup or pick.get("Matchup", ""),
                "league": league,
                "date": pick.get("Date", ""),
            })
        
        # Find consensus (2+ sources on same side)
        consensus_plays = []
        
        for key, group in groups.items():
            # Deduplicate sources (clean and unique)
            sources_list = []
            seen_sources = set()
            for p in group:
                src = self.clean_source(p["source"])
                if src and src.lower() not in seen_sources:
                    sources_list.append(src)
                    seen_sources.add(src.lower())
            
            if len(sources_list) < min_sources:
                continue
            
            # Build consensus record
            first = group[0]
            pick_type = first["pick_type"]
            
            # Calculate average line ONLY for same pick types
            # And only for spreads/totals (not ML)
            avg_line = None
            if pick_type in ("spread", "total"):
                lines = [p["line"] for p in group if p["line"] is not None and p["pick_type"] == pick_type]
                if lines:
                    avg_line = sum(lines) / len(lines)
                    # Round to reasonable precision
                    if pick_type == "spread":
                        # Round spread to nearest 0.5
                        avg_line = round(avg_line * 2) / 2
                    else:
                        # Round total to nearest 0.5
                        avg_line = round(avg_line * 2) / 2
            
            # Find the best matchup (non-empty, most complete)
            best_matchup = ""
            for p in group:
                m = p.get("matchup", "")
                if m and m.upper() != "UNKNOWN":
                    if not best_matchup or ("@" in m and "@" not in best_matchup):
                        best_matchup = m
            
            # Skip if no valid matchup found
            if not best_matchup:
                logger.warning(f"Skipping consensus with no matchup: {key}")
                continue
            
            # Determine the side description
            if pick_type == "spread" and avg_line is not None:
                side = f"{first['team']} {avg_line:+.1f}"
            elif pick_type == "ml":
                side = f"{first['team']} ML"
            elif pick_type == "total":
                side = f"{first['team']} {avg_line:.1f}" if avg_line else first['team']
            else:
                side = first["pick"]
            
            # Generate unique ID
            cons_id = hashlib.md5(f"{key}_{first['date']}".encode()).hexdigest()[:12]
            
            consensus_plays.append({
                "consensus_id": f"cons_{cons_id}",
                "date": first["date"],
                "league": first["league"],
                "matchup": best_matchup,
                "side": side,
                "sources": ", ".join(sorted(sources_list)),
                "strength": len(sources_list),
                "avg_line": avg_line,
                "result": "",
                "profit_loss": "",
                "alerted": False,
                "created_at": datetime.now(TIMEZONE).isoformat(),
            })
        
        # Sort by strength (highest first)
        consensus_plays.sort(key=lambda x: x["strength"], reverse=True)
        
        logger.info(f"Found {len(consensus_plays)} consensus plays")
        return consensus_plays
    
    def write_consensus(self, consensus_plays: List[Dict]) -> int:
        """Write consensus plays to the Consensus sheet."""
        if not consensus_plays:
            return 0
        
        ws = self.spreadsheet.worksheet("Consensus")
        
        # Get existing consensus IDs to avoid duplicates
        existing = ws.get_all_records()
        existing_ids = set(row.get("consensus_id", "") for row in existing)
        
        # Filter out duplicates
        new_plays = [c for c in consensus_plays if c["consensus_id"] not in existing_ids]
        
        if not new_plays:
            logger.info("No new consensus plays to add")
            return 0
        
        # Prepare rows
        rows = []
        for c in new_plays:
            rows.append([
                c["consensus_id"],
                c["date"],
                c["league"],
                c["matchup"],
                c["side"],
                c["sources"],
                c["strength"],
                c["avg_line"] if c["avg_line"] else "",
                c["result"],
                c["profit_loss"],
                c["alerted"],
                c["created_at"],
            ])
        
        ws.append_rows(rows, value_input_option='USER_ENTERED')
        logger.info(f"Added {len(rows)} consensus plays to sheet")
        
        return len(rows)
    
    def run(self, date_str: str = None) -> Dict:
        """
        Run the full consensus scan.
        
        Args:
            date_str: Date in YYYY-MM-DD format (default: today)
        
        Returns:
            Stats dictionary
        """
        if date_str is None:
            date_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
        
        logger.info(f"Scanning for consensus on {date_str}")
        
        # Get picks
        picks = self.get_picks_for_date(date_str)
        
        if not picks:
            logger.warning("No picks found for date")
            return {"date": date_str, "picks": 0, "consensus": 0, "written": 0}
        
        # Detect consensus
        consensus = self.detect_consensus(picks)
        
        # Write to sheet
        written = self.write_consensus(consensus)
        
        return {
            "date": date_str,
            "picks": len(picks),
            "consensus": len(consensus),
            "written": written,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=" + 
                        str(self.spreadsheet.worksheet("Consensus").id)
        }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scan for consensus picks")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--days", type=int, default=1, help="Number of days to scan back")
    args = parser.parse_args()
    
    scanner = ConsensusScanner()
    
    if args.date:
        stats = scanner.run(args.date)
        print(f"\n{'='*50}")
        print(f"Consensus Scan - {stats['date']}")
        print(f"{'='*50}")
        print(f"Picks scanned:    {stats['picks']}")
        print(f"Consensus found:  {stats['consensus']}")
        print(f"New records:      {stats['written']}")
        print(f"\nView: {stats.get('sheet_url', '')}")
    else:
        # Scan today and optionally back N days
        for i in range(args.days):
            date = (datetime.now(TIMEZONE) - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = scanner.run(date)
            print(f"{date}: {stats['consensus']} consensus plays ({stats['written']} new)")


if __name__ == "__main__":
    main()
