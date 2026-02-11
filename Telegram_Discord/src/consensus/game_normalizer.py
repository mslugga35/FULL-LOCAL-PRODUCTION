"""
Game Normalizer
Standardizes team names, game IDs, and pick formats for consensus matching.
"""

import re
import hashlib
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import pytz

from .team_mappings import normalize_team, get_team_display_name

TIMEZONE = pytz.timezone("America/New_York")


def extract_line(pick_text: str) -> Tuple[Optional[float], str]:
    """
    Extract the line/spread from a pick string.
    
    Args:
        pick_text: Raw pick text like "Bulls -5.5" or "Lakers +3"
    
    Returns:
        Tuple of (line_value, pick_type)
        pick_type: "spread", "ml", "total", "prop"
    """
    if not pick_text:
        return (None, "unknown")
    
    text_lower = pick_text.lower()
    
    # Check for over/under (totals)
    if "over" in text_lower or "under" in text_lower or "o/u" in text_lower:
        # Extract number after over/under
        match = re.search(r'(?:over|under|o|u)\s*(\d+\.?\d*)', text_lower)
        if match:
            return (float(match.group(1)), "total")
        return (None, "total")
    
    # Check for moneyline
    if "ml" in text_lower or "moneyline" in text_lower or "money line" in text_lower:
        return (None, "ml")
    
    # Check for spread (team +/- number)
    # Matches patterns like: "Bulls -5.5", "-5.5", "+3", "Team -7½"
    spread_pattern = r'([+-]?\s*\d+\.?\d*)'
    match = re.search(spread_pattern, pick_text)
    if match:
        line_str = match.group(1).replace(" ", "").replace("½", ".5")
        try:
            return (float(line_str), "spread")
        except ValueError:
            pass
    
    # Check for player props
    prop_keywords = ["points", "rebounds", "assists", "yards", "touchdowns", "strikeouts", "pts", "reb", "ast"]
    if any(kw in text_lower for kw in prop_keywords):
        match = re.search(r'(\d+\.?\d*)', pick_text)
        if match:
            return (float(match.group(1)), "prop")
        return (None, "prop")
    
    # Default to moneyline if no line found
    return (None, "ml")


def extract_team_from_pick(pick_text: str, sport: str = None) -> Tuple[str, str]:
    """
    Extract the team name from a pick string.
    
    Args:
        pick_text: Raw pick text like "Bulls -5.5" or "Lakers ML"
        sport: Sport to help with team lookup
    
    Returns:
        Tuple of (normalized_team_code, display_name)
    """
    if not pick_text:
        return ("", "")
    
    # Remove common suffixes and numbers
    cleaned = re.sub(r'[+-]\s*\d+\.?\d*', '', pick_text)  # Remove spread
    cleaned = re.sub(r'\s*(ml|moneyline|money line|pk|even)\s*', ' ', cleaned, flags=re.I)
    cleaned = re.sub(r'\s*\(.*?\)', '', cleaned)  # Remove parenthetical
    cleaned = re.sub(r'\s*(over|under|o|u)\s*\d*\.?\d*', '', cleaned, flags=re.I)  # Remove o/u
    cleaned = cleaned.strip()
    
    if not cleaned:
        return ("", "")
    
    # Try to normalize the team name
    code, detected_sport = normalize_team(cleaned, sport)
    
    if detected_sport:
        display = get_team_display_name(code, detected_sport)
        return (code, display)
    
    return (cleaned, cleaned)


def parse_game_matchup(game_text: str, sport: str = None) -> Dict[str, str]:
    """
    Parse a game matchup string into away and home teams.
    
    Args:
        game_text: Matchup like "Bulls vs Pistons", "CHI @ DET", "Lakers at Celtics"
    
    Returns:
        Dict with keys: away, home, away_code, home_code
    """
    if not game_text:
        return {"away": "", "home": "", "away_code": "", "home_code": ""}
    
    # Split on common separators
    separators = [" @ ", " at ", " vs ", " vs. ", " v ", " - "]
    teams = []
    
    for sep in separators:
        if sep.lower() in game_text.lower():
            parts = re.split(sep, game_text, flags=re.I)
            if len(parts) == 2:
                teams = [p.strip() for p in parts]
                break
    
    if len(teams) != 2:
        return {"away": game_text, "home": "", "away_code": "", "home_code": ""}
    
    away_code, _ = normalize_team(teams[0], sport)
    home_code, _ = normalize_team(teams[1], sport)
    
    return {
        "away": teams[0],
        "home": teams[1],
        "away_code": away_code,
        "home_code": home_code,
    }


def generate_game_id(away_team: str, home_team: str, date_str: str, sport: str = None) -> str:
    """
    Generate a unique game ID for matching picks to games.
    
    Format: {AWAY}@{HOME}_{YYYY-MM-DD}
    Example: CHI@DET_2026-02-03
    
    Args:
        away_team: Away team name or code
        home_team: Home team name or code
        date_str: Date string (YYYY-MM-DD format)
        sport: Optional sport for normalization
    
    Returns:
        Unique game ID string
    """
    away_code, _ = normalize_team(away_team, sport)
    home_code, _ = normalize_team(home_team, sport)
    
    return f"{away_code}@{home_code}_{date_str}"


def generate_consensus_id(game_id: str, pick_side: str, line: float = None) -> str:
    """
    Generate a unique consensus ID for grouping picks.
    
    Format: cons_{TEAM}{LINE}_{DATE}
    Example: cons_CHI-5.5_2026-02-03
    
    Args:
        game_id: Game ID from generate_game_id
        pick_side: Team being picked
        line: Spread line (optional)
    
    Returns:
        Unique consensus ID
    """
    team_code, _ = normalize_team(pick_side)
    
    if line is not None:
        line_str = f"{line:+.1f}".replace("+", "").replace("-", "m")  # m for minus
        if line >= 0:
            line_str = f"p{line:.1f}"  # p for plus
    else:
        line_str = "ML"
    
    # Extract date from game_id
    date_part = game_id.split("_")[-1] if "_" in game_id else datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    
    return f"cons_{team_code}{line_str}_{date_part}"


def normalize_pick(raw_pick: Dict[str, Any], date_str: str = None) -> Dict[str, Any]:
    """
    Fully normalize a raw pick into a standardized format.
    
    Args:
        raw_pick: Raw pick data from vision processor
            Expected keys: capper, sport, game, pick, odds, units
        date_str: Date for the pick (YYYY-MM-DD)
    
    Returns:
        Normalized pick dictionary ready for Sheets
    """
    if date_str is None:
        date_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    
    sport = raw_pick.get("sport", "").upper()
    
    # Parse the game matchup
    game_info = parse_game_matchup(raw_pick.get("game", ""), sport)
    
    # Extract the pick details
    pick_text = raw_pick.get("pick", "")
    team_code, team_display = extract_team_from_pick(pick_text, sport)
    line, pick_type = extract_line(pick_text)
    
    # Generate IDs
    game_id = generate_game_id(
        game_info.get("away", ""),
        game_info.get("home", ""),
        date_str,
        sport
    )
    
    # Determine pick side for consensus
    pick_side = team_code if team_code else pick_text
    
    # Generate pick ID (unique per message)
    msg_id = raw_pick.get("msg_id", "")
    pick_hash = hashlib.md5(f"{msg_id}_{pick_text}".encode()).hexdigest()[:8]
    pick_id = f"pick_{date_str}_{pick_hash}"
    
    # Parse odds
    odds_raw = raw_pick.get("odds", "")
    try:
        odds = int(str(odds_raw).replace("+", ""))
    except (ValueError, TypeError):
        odds = -110  # Default
    
    # Parse units
    units_raw = raw_pick.get("units", "")
    try:
        # Handle "2U", "2 units", "2-Unit", etc.
        units_match = re.search(r'(\d+\.?\d*)', str(units_raw))
        units = float(units_match.group(1)) if units_match else 1.0
    except (ValueError, TypeError):
        units = 1.0
    
    # Build normalized pick
    normalized = {
        "pick_id": pick_id,
        "date": date_str,
        "time": raw_pick.get("time", datetime.now(TIMEZONE).strftime("%H:%M:%S")),
        "capper": raw_pick.get("capper", "Unknown"),
        "sport": sport,
        "game": f"{game_info.get('away_code', game_info.get('away'))} @ {game_info.get('home_code', game_info.get('home'))}",
        "pick": pick_text,
        "pick_team": team_code,
        "pick_side": pick_side,
        "pick_type": pick_type,
        "line": line,
        "odds": odds,
        "units": units,
        "confidence": raw_pick.get("confidence", ""),
        "result": "",
        "profit_loss": "",
        "game_id": game_id,
        "consensus_id": "",  # Set later by consensus detector
        "msg_id": msg_id,
        "raw_text": raw_pick.get("raw_text", pick_text),
    }
    
    return normalized


def are_same_side(pick1: Dict, pick2: Dict) -> bool:
    """
    Check if two picks are on the same side of a game.
    
    Args:
        pick1: First normalized pick
        pick2: Second normalized pick
    
    Returns:
        True if both picks are backing the same side
    """
    # Must be same game
    if pick1.get("game_id") != pick2.get("game_id"):
        return False
    
    # Must be same pick type (both spreads, both ML, etc.)
    if pick1.get("pick_type") != pick2.get("pick_type"):
        return False
    
    # For spreads/ML, check if same team
    if pick1.get("pick_type") in ("spread", "ml"):
        return pick1.get("pick_team") == pick2.get("pick_team")
    
    # For totals, check if both over or both under
    if pick1.get("pick_type") == "total":
        p1_over = "over" in pick1.get("raw_text", "").lower()
        p2_over = "over" in pick2.get("raw_text", "").lower()
        return p1_over == p2_over
    
    return False
