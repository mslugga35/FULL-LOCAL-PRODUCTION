"""
Consensus Detector
Groups picks by game and side to identify consensus plays (2+ cappers on same side).
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
import pytz

from .game_normalizer import are_same_side, generate_consensus_id

logger = logging.getLogger(__name__)
TIMEZONE = pytz.timezone("America/New_York")


class ConsensusDetector:
    """Detects consensus plays from a list of normalized picks."""
    
    def __init__(self, min_cappers: int = 2):
        """
        Initialize detector.
        
        Args:
            min_cappers: Minimum cappers required for consensus (default: 2)
        """
        self.min_cappers = min_cappers
    
    def detect(self, picks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect consensus plays from a list of picks.
        
        Args:
            picks: List of normalized pick dictionaries
        
        Returns:
            List of consensus records
        """
        if not picks:
            return []
        
        # Group picks by game_id first
        games = defaultdict(list)
        for pick in picks:
            game_id = pick.get("game_id", "")
            if game_id:
                games[game_id].append(pick)
        
        consensus_list = []
        
        for game_id, game_picks in games.items():
            if len(game_picks) < self.min_cappers:
                continue
            
            # Within each game, group by side
            sides = self._group_by_side(game_picks)
            
            for side_key, side_picks in sides.items():
                if len(side_picks) >= self.min_cappers:
                    consensus = self._create_consensus_record(side_picks)
                    if consensus:
                        consensus_list.append(consensus)
                        
                        # Update picks with consensus_id
                        for pick in side_picks:
                            pick["consensus_id"] = consensus["consensus_id"]
        
        # Sort by strength (highest first)
        consensus_list.sort(key=lambda x: x.get("strength", 0), reverse=True)
        
        logger.info(f"Detected {len(consensus_list)} consensus plays from {len(picks)} picks")
        return consensus_list
    
    def _group_by_side(self, picks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group picks by which side they're on.
        
        Returns dict where key is a side identifier and value is list of picks on that side.
        """
        sides = defaultdict(list)
        assigned = set()
        
        for i, pick in enumerate(picks):
            if i in assigned:
                continue
            
            # Start a new group with this pick
            side_key = f"{pick.get('game_id')}_{pick.get('pick_team')}_{pick.get('pick_type')}"
            sides[side_key].append(pick)
            assigned.add(i)
            
            # Find other picks on same side
            for j, other in enumerate(picks):
                if j in assigned:
                    continue
                if are_same_side(pick, other):
                    sides[side_key].append(other)
                    assigned.add(j)
        
        return sides
    
    def _create_consensus_record(self, picks: List[Dict]) -> Dict[str, Any]:
        """Create a consensus record from a group of picks."""
        if not picks:
            return None
        
        first = picks[0]
        
        # Get unique cappers
        cappers = list(set(p.get("capper", "Unknown") for p in picks))
        
        # Calculate average line
        lines = [p.get("line") for p in picks if p.get("line") is not None]
        avg_line = sum(lines) / len(lines) if lines else None
        
        # Generate consensus ID
        consensus_id = generate_consensus_id(
            first.get("game_id", ""),
            first.get("pick_team", ""),
            avg_line
        )
        
        # Build the pick side description
        if first.get("pick_type") == "spread" and avg_line is not None:
            side = f"{first.get('pick_team')} {avg_line:+.1f}"
        elif first.get("pick_type") == "ml":
            side = f"{first.get('pick_team')} ML"
        elif first.get("pick_type") == "total":
            over_under = "Over" if "over" in first.get("raw_text", "").lower() else "Under"
            side = f"{over_under} {avg_line}" if avg_line else over_under
        else:
            side = first.get("pick", "")
        
        return {
            "consensus_id": consensus_id,
            "date": first.get("date", datetime.now(TIMEZONE).strftime("%Y-%m-%d")),
            "sport": first.get("sport", ""),
            "game": first.get("game", ""),
            "game_id": first.get("game_id", ""),
            "side": side,
            "pick_type": first.get("pick_type", ""),
            "cappers": cappers,
            "pick_ids": [p.get("pick_id") for p in picks],
            "strength": len(cappers),
            "avg_line": avg_line,
            "avg_units": sum(p.get("units", 1) for p in picks) / len(picks),
            "result": "",
            "alerted": False,
        }
    
    def get_opposing_picks(self, picks: List[Dict], consensus: Dict) -> List[Dict]:
        """
        Find picks that are on the opposite side of a consensus play.
        
        Args:
            picks: All picks for the day
            consensus: A consensus record
        
        Returns:
            List of picks that fade the consensus
        """
        opposing = []
        consensus_cappers = set(consensus.get("cappers", []))
        game_id = consensus.get("game_id", "")
        
        for pick in picks:
            if pick.get("game_id") != game_id:
                continue
            
            if pick.get("capper") in consensus_cappers:
                continue
            
            # Check if this pick is on the opposite side
            # For spreads/ML, opposite team
            # For totals, opposite direction
            if pick.get("pick_type") == consensus.get("pick_type"):
                if pick.get("pick_type") in ("spread", "ml"):
                    if pick.get("pick_team") != consensus.get("side", "").split()[0]:
                        opposing.append(pick)
                elif pick.get("pick_type") == "total":
                    pick_over = "over" in pick.get("raw_text", "").lower()
                    consensus_over = "over" in consensus.get("side", "").lower()
                    if pick_over != consensus_over:
                        opposing.append(pick)
        
        return opposing


def detect_consensus(picks: List[Dict], min_cappers: int = 2) -> List[Dict]:
    """
    Convenience function to detect consensus without creating detector instance.
    
    Args:
        picks: List of normalized picks
        min_cappers: Minimum cappers for consensus
    
    Returns:
        List of consensus records
    """
    detector = ConsensusDetector(min_cappers=min_cappers)
    return detector.detect(picks)
