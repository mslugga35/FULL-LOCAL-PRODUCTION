# src/utils/picks_formatter.py
import re
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, date
import pytz

# State directory for dedup database
STATE_DIR = Path(__file__).parent.parent.parent / "state"
STATE_DIR.mkdir(exist_ok=True)
DEDUP_DB_PATH = STATE_DIR / "pick_hashes.sqlite3"

# Initialize dedup database
def _init_dedup_db():
    """Initialize SQLite database for pick deduplication by content hash"""
    db = sqlite3.connect(str(DEDUP_DB_PATH), check_same_thread=False)
    db.execute("""
        CREATE TABLE IF NOT EXISTS seen_picks (
            content_hash TEXT PRIMARY KEY,
            capper TEXT,
            pick_preview TEXT,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_first_seen ON seen_picks(first_seen)")
    # Purge entries older than 7 days
    db.execute("DELETE FROM seen_picks WHERE first_seen < datetime('now', '-7 days')")
    db.commit()
    return db

_dedup_db = None

def get_dedup_db():
    """Get or create dedup database connection"""
    global _dedup_db
    if _dedup_db is None:
        _dedup_db = _init_dedup_db()
    return _dedup_db


def compute_pick_hash(capper: str, text: str) -> str:
    """Compute MD5 hash of capper + normalized pick text"""
    # Normalize: lowercase, remove extra whitespace, remove odds variations
    normalized = re.sub(r'\s+', ' ', (capper or '').lower() + '|' + (text or '').lower()).strip()
    # Remove odds that might vary slightly (-110 vs -115)
    normalized = re.sub(r'[+-]\d{3}', '', normalized)
    return hashlib.md5(normalized.encode()).hexdigest()


def is_duplicate_pick(capper: str, text: str) -> bool:
    """Check if this pick has been seen before (by content hash)"""
    content_hash = compute_pick_hash(capper, text)
    db = get_dedup_db()
    cursor = db.execute("SELECT 1 FROM seen_picks WHERE content_hash = ?", (content_hash,))
    return cursor.fetchone() is not None


def record_pick(capper: str, text: str):
    """Record a pick's hash to prevent future duplicates"""
    content_hash = compute_pick_hash(capper, text)
    db = get_dedup_db()
    try:
        preview = (text or '')[:100]
        db.execute(
            "INSERT OR IGNORE INTO seen_picks (content_hash, capper, pick_preview) VALUES (?, ?, ?)",
            (content_hash, capper or 'Unknown', preview)
        )
        db.commit()
    except Exception:
        pass  # Ignore dedup errors


# ---- Recap detection patterns (Phase 1) ----
RECAP_PATTERNS = [
    re.compile(r'\byesterday\s+we\s+went\b', re.I),           # "yesterday we went 3-1"
    re.compile(r'\brecap\b', re.I),                           # "recap" anywhere
    re.compile(r'\brecord[:\s]+\d+-\d+', re.I),               # "record: 45-30"
    re.compile(r'\bhit\s+\d+/\d+\s+yesterday\b', re.I),       # "hit 3/4 yesterday"
    re.compile(r'\bwent\s+\d+-\d+\s+yesterday\b', re.I),      # "went 3-1 yesterday"
    re.compile(r"\byesterday['\u2019]?s?\s+(picks?|plays?|results?)\b", re.I),  # "yesterday's picks"
    re.compile(r'\blast\s+night\s+we\b', re.I),               # "last night we"
    re.compile(r'\b\d+-\d+\s+run\b', re.I),                   # "10-4 run"
    re.compile(r'\bcashed\s+\d+/\d+\b', re.I),                # "cashed 3/4"
]

# ---- OCR Result Detection Patterns (bet slips, receipts, results) ----
OCR_RESULT_PATTERNS = [
    # === OUTCOME INDICATORS (checkmarks/X marks) ===
    re.compile(r'[\u2705\u2611\u2714]'),              # ✅ ☑️ ✔️ (won/hit)
    re.compile(r'[\u274C\u274E]'),                     # ❌ ❎ (lost/miss)

    # === BET STATUS TEXT ===
    re.compile(r'\bWon\b', re.I),                      # "Celtics -6.5 Won"
    re.compile(r'\bLost\b', re.I),                     # "Lakers +3 Lost"
    re.compile(r'\bPush\b', re.I),                     # Push = tie
    re.compile(r'\bVoid(ed)?\b', re.I),                # Voided bet
    re.compile(r'\bWINNER\b', re.I),                   # "WINNER" tag
    re.compile(r'\bLOSER\b', re.I),                    # "LOSER" tag
    re.compile(r'\bCASHED\b', re.I),                   # "CASHED" result
    re.compile(r'\bBUST(ED)?\b', re.I),                # "BUSTED" loss
    re.compile(r'\bFinished\b', re.I),                 # Game finished
    re.compile(r'\bSettled\b', re.I),                  # Bet settled
    re.compile(r'\bGraded\b', re.I),                   # Bet graded
    re.compile(r'\bCompleted\b', re.I),                # Completed

    # === PAYOUT INDICATORS ===
    re.compile(r'\$[\d,]+\.?\d*\s*(WON|WIN|PROFIT|PAYOUT)', re.I),   # "$916.67 WON"
    re.compile(r'(WON|PROFIT|PAYOUT)\s+\$[\d,]+', re.I),             # "WON $916.67"
    re.compile(r'WON\s+ON\s+(FANDUEL|DRAFTKINGS|BETMGM|CAESARS|BET365|HARD\s*ROCK|BARSTOOL|POINTSBET|BETRIVERS)', re.I),
    re.compile(r'(PROFIT|PAYOUT|WINNINGS|TO\s+WIN)[:\s]+\$[\d,]+', re.I),

    # === RECEIPT/HISTORY SCREENS ===
    re.compile(r'Transaction\s+History', re.I),
    re.compile(r'BET\s+ID[:\s]*[\d/]+', re.I),         # "BET ID: 0/0111809/0006423"
    re.compile(r'Bet\s+(Receipt|Slip|History)', re.I),
    re.compile(r'\bPLACED[:\s]', re.I),                # "PLACED: 1/26/2026"

    # === CELEBRATION/POST-RESULT TEXT ===
    re.compile(r'\bon\s+point\b', re.I),               # "You been on point!!!"
    re.compile(r'\bsomething\s+light\b', re.I),        # "something light 🔥"
    re.compile(r'\b(great|nice|big)\s+(hit|win|cash)\b', re.I),
    re.compile(r'\bthanks\s+(a\s+lot|cuz|bro)', re.I),
    re.compile(r'\blet.?s\s+go\b', re.I),              # "let's go!"
    re.compile(r'\bstay\s+hot\b', re.I),               # "STAY HOT"

    # === STATS/CHANNEL METRICS SCREENSHOTS ===
    re.compile(r'Total\s+Customers', re.I),
    re.compile(r'\d+\.?\d*K?\s+Hits\b', re.I),         # "812 Hits"
    re.compile(r'\bCommission[:\s]', re.I),
    re.compile(r'First\s+Deposit', re.I),
    re.compile(r'\bSignups?\b', re.I),
    re.compile(r'All\s+channels', re.I),               # Channel stats view

    # === BET SLIP INDICATORS (placed bets, not picks) ===
    re.compile(r'\bStake[:\s]+[\$\w]', re.I),          # "Stake: CA$1,000.00"
    re.compile(r'\bWager[:\s]+\$', re.I),              # "Wager: $150.00"
    re.compile(r'\bRisk[:\s]+\$', re.I),               # "Risk: $100"
    re.compile(r'\bTo\s+Win[:\s]+\$', re.I),           # "To Win: $90.91"
    re.compile(r'\bPotential\s+(Payout|Win)', re.I),   # "Potential Payout"

    # === OCR ERROR MESSAGES ===
    re.compile(r'no\s+sports?\s+picks?\s+in', re.I),   # "no sports picks in the provided image"
    re.compile(r'channel\s+statistics', re.I),         # "channel statistics, not sports betting"
    re.compile(r'not\s+sports?\s+betting', re.I),      # "not sports betting picks"
    re.compile(r'displays?\s+channel', re.I),          # "displays channel statistics"

    # === GEMINI RESULT DETECTION ===
    re.compile(r'\[RESULT_SCREENSHOT\]', re.I),        # Gemini detected this is a result
    re.compile(r'RESULT_SCREENSHOT', re.I),            # Without brackets
]


def get_today_ny():
    """Get today's date in NY timezone"""
    ny_tz = pytz.timezone('America/New_York')
    return datetime.now(ny_tz).date()


def extract_dates_from_text(text):
    """
    Extract all dates from OCR text.
    Returns list of date objects.
    """
    dates = []

    # M/D/YYYY - "1/26/2026"
    for m in re.finditer(r'(\d{1,2})/(\d{1,2})/(\d{4})', text):
        try:
            dates.append(date(int(m.group(3)), int(m.group(1)), int(m.group(2))))
        except ValueError:
            pass

    # M/D/YY - "1/26/26"
    for m in re.finditer(r'(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)', text):
        try:
            year = int(m.group(3))
            year = 2000 + year if year < 50 else 1900 + year
            dates.append(date(year, int(m.group(1)), int(m.group(2))))
        except ValueError:
            pass

    # M-D-YYYY - "1-26-2026"
    for m in re.finditer(r'(\d{1,2})-(\d{1,2})-(\d{4})', text):
        try:
            dates.append(date(int(m.group(3)), int(m.group(1)), int(m.group(2))))
        except ValueError:
            pass

    # YYYY-MM-DD - "2026-01-26"
    for m in re.finditer(r'(\d{4})-(\d{1,2})-(\d{1,2})', text):
        try:
            dates.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            pass

    return dates


def contains_past_date(text):
    """
    Check if text contains any date BEFORE today.

    - Today's date: OK (could be today's pick with timestamp)
    - Future date: OK (advance pick)
    - Past date: SKIP (result from yesterday)
    """
    today = get_today_ny()

    for found_date in extract_dates_from_text(text):
        if found_date < today:
            return True

    return False


def is_final_score(text):
    """
    Detect final game scores in OCR text.

    Must distinguish from:
    - Odds like -110, +150 (have +/- prefix)
    - Spreads like -6.5, +3.5 (have decimal)

    Returns True if text contains what looks like a final score.
    """
    # Pattern: two 2-3 digit numbers separated by dash
    # NOT preceded by +/- (that's odds)
    # NOT followed by decimal (that's spread)
    score_pattern = re.compile(
        r'(?<![+-])(?<!\d)(\d{2,3})\s*[-–]\s*(\d{2,3})(?!\.)(?!\d)'
    )

    for match in score_pattern.finditer(text):
        s1, s2 = int(match.group(1)), int(match.group(2))

        # Validate as realistic game score
        is_basketball = (70 <= s1 <= 160) and (70 <= s2 <= 160)
        is_football = (0 <= s1 <= 70) and (0 <= s2 <= 70) and (s1 != s2)

        # Exclude common odds that might slip through
        common_odds = {100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150}
        if s1 in common_odds and s2 in common_odds:
            continue

        if is_basketball or is_football:
            return True

    # Quarter/period scores: "11 26 28 29" or "32 20 23 27"
    quarter_pattern = re.compile(r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\b')
    for match in quarter_pattern.finditer(text):
        quarters = [int(match.group(i)) for i in range(1, 5)]
        # Basketball quarters: typically 15-40 each
        if all(10 <= q <= 45 for q in quarters):
            return True

    return False


def is_ocr_result(text):
    """
    Check if OCR text is from a RESULT screenshot (bet slip showing outcome).

    Checks three layers:
    - Layer 1: Status keywords (Won, Lost, ✅, ❌, Finished...)
    - Layer 2: Final scores (94-102)
    - Layer 3: Past dates (yesterday's date)

    Returns True if ANY layer indicates a result.
    """
    if not text:
        return False

    # Layer 1: Keyword patterns
    for pattern in OCR_RESULT_PATTERNS:
        if pattern.search(text):
            return True

    # Layer 2: Final scores
    if is_final_score(text):
        return True

    # Layer 3: Past dates
    if contains_past_date(text):
        return True

    return False


def is_recap_message(text: str) -> bool:
    """
    Check if message is a recap/results post (not actual picks).

    Combines:
    - Text-based recap patterns (yesterday we went, record, etc)
    - OCR result detection (Won, ✅, ❌, scores, past dates)
    """
    if not text:
        return False

    # Text-based recap patterns
    for pattern in RECAP_PATTERNS:
        if pattern.search(text):
            return True

    # OCR result patterns (direct check, no recursion)
    for pattern in OCR_RESULT_PATTERNS:
        if pattern.search(text):
            return True

    # Final scores check
    if is_final_score(text):
        return True

    # Past dates check
    if contains_past_date(text):
        return True

    return False

# ---- Canonical capper names (your list, cleaned) ----
KNOWN_CAPPERS = [
    "A11 Bets","AMPM","Action Network","AlgoPicks","Analytics Capper","ANON","Bankroll Bill",
    "BeezoWins","Bet Sharper","Blink Bets","BrandonTheProfit","BulliesPicks","CashCing","Cblez","Cesar",
    "Cody Covers Spreads","Darth Fader","Dirty Bubble Bets","Dommy Locked","Dormroom Degenerates",
    "DPatt","DquanPicks","DuckInvestments","Fern","Glitch Whale","Hammering Hank","Illicit Picks","ISW",
    "Itstroywest","Kims Picks","Kleos","Kingcap","LaFormula","Lear Locks","Match Point Bets",
    "MatthewP07","McBets","MidwestMikeSports","Monumental","Mr Big Bets","Nicky Cashin",
    "NCSharp","Newmark","NRFI Algorithm","Out of Line Bets","PARLAY P","PardonMyPick","PickzHub",
    "Picks 4 Dayzzz","Platinum Locks","PorterPicks","PremPod","ProvenWinner","RBSSportsPlays",
    "Relentless Sports Consulting","RickyPick","Ronald Cabang","SBK (Chips)","Sean Perry Wins",
    "SeekingReturns","Set Point Bets","Sharp Investments","SmartMoneySports","SPS","TBSportsBetting",
    "The Betting Queen","The Gold Sheet","The Guru","The Gambling Gawd","The Sharp Sheets","This Girl Betz","TMS",
    "Travy","TrellJSports","UTAB","VC","Vezino Locks","Vinny","YourDailyCapper","ZachsBets",
    "vegasmirabet","VegasClub","THB OCR"
]

# ---- Alias → canonical (case-insensitive keys) ----
ALIASES = {
    "cblez": "Cblez",
    "cblez.": "Cblez",
    "nickycashin": "Nicky Cashin",
    "platinumlocks": "Platinum Locks",
    "cabang": "Ronald Cabang",
    "cabang (ronald cabang)": "Ronald Cabang",
    "sbk": "SBK (Chips)",
    "yourdailycapper": "YourDailyCapper",
    "ncsharp": "NCSharp",
    "uatb": "UTAB",
    "thb": "THB OCR",
    "vegas club": "VegasClub",
    "vegasclub": "VegasClub",
    "vegas mira bet": "vegasmirabet",
    "vegasmira": "vegasmirabet",
    "vegas_mira_bet": "vegasmirabet",
    "seekingreturns": "SeekingReturns",
    "seeking returns": "SeekingReturns",
    "seanperrywins": "Sean Perry Wins",
    "sean perry wins": "Sean Perry Wins",
    "codycoverspreads": "Cody Covers Spreads",
    "thebettingqueen": "The Betting Queen",
    "matchpointbets": "Match Point Bets",
    "setpointbets": "Set Point Bets",
    "outoflinebets": "Out of Line Bets",
    "a11bets": "A11 Bets",
    "theguru": "The Guru",
    "bankrollbill": "Bankroll Bill",
    "smartmoneysports": "SmartMoneySports",
    "darthfader": "Darth Fader",
    "cashcing": "CashCing",
    "trelljsports": "TrellJSports",
    "midwestmikesports": "MidwestMikeSports",
    "duckinvestments": "DuckInvestments",
    "learlocks": "Lear Locks",
    "zachsbets": "ZachsBets",
    "kimspicks": "Kims Picks",
    "porterpicks": "PorterPicks",
}

# ---- Noise patterns (headers, promos, separators, emoji spam) ----
NOISE_PATTERNS = [
    re.compile(r'\bCAPPERS?\s*FREE\b.*', re.I),
    re.compile(r'\bFREE\s*(VIP|PICKS?)\b.*', re.I),
    re.compile(r'\b(package|join|subscribe|cheapest|prices?|dm\s*(me)?|contact)\b.*', re.I),
    re.compile(r'DM\s*([➡➜➔→]+|->)?\s*[✅☑️✔️]?\s*@?\w*', re.I),
    re.compile(r'@cappers?free', re.I),
    re.compile(r'@persfree', re.I),
    re.compile(r'@srcgroup', re.I),
    re.compile(r'@everyone', re.I),
    re.compile(r'@[a-z]+free\b', re.I),  # catches @sfree, @rstree, etc.
    re.compile(r'Data Extractor Bot', re.I),
    re.compile(r'\bAPP\b\s*—', re.I),
    re.compile(r'Yesterday at \d+:\d+\s*(AM|PM)', re.I),
    re.compile(r'^\d{1,2}:\d{2}\s*(am|pm)?$', re.I),
    re.compile(r'[➖─—\-=._•*|·]{3,}'),  # long separators
    re.compile(r'[\u26A0\u2757\u26D4]'),  # ⚠️❗⛔ (keep ✅❌ for result detection)
    re.compile(r'\bstake\.com\b', re.I),
    re.compile(r'Browse\s+Casino', re.I),
    re.compile(r'Bet\s+Slip', re.I),
    re.compile(r'Sports\s+Chat', re.I),
    re.compile(r'View\s+All.*', re.I),
    re.compile(r'Total\s+(wager|payout|potential)', re.I),
    re.compile(r'Risk\s*/\s*Win', re.I),
]

TEAM_HINT = re.compile(
    r'\b(Lakers|Warriors|Yankees|Dodgers|Patriots|Chiefs|Arsenal|Real\s*Madrid|Barcelona|PSG|Celtics|Knicks|Braves|Cowboys|Dolphins|Bills|Marlins|Twins|Athletics|Royals)\b',
    re.I
)

def _normalize_text(t: str) -> str:
    if not t: return ""

    # First pass: Remove CAPPERS FREE and its variations completely
    t = re.sub(r'CAPPERS?\s*FREE[^\n]*', '', t, flags=re.I)
    t = re.sub(r'^.*CAPPERS?\s*FREE.*$', '', t, flags=re.I | re.MULTILINE)

    # Remove lines with just emoji or noise
    t = re.sub(r'^[💥🔥⚡️🎯🏆💰💵🤑💸🚀📸]*$', '', t, flags=re.MULTILINE)

    # Remove @ mentions for spam accounts and noise
    t = re.sub(r'@cappers?free', '', t, flags=re.I)
    t = re.sub(r'@persfree', '', t, flags=re.I)
    t = re.sub(r'@srcgroup.*?(?=\n|$)', '', t, flags=re.I)  # Remove @srcgroup and timestamps
    t = re.sub(r'@everyone', '', t, flags=re.I)
    t = re.sub(r'@[a-z]+free\b', '', t, flags=re.I)
    t = re.sub(r'@@\w+', '', t, flags=re.I)  # double @ patterns
    t = re.sub(r'@cappers\b', '', t, flags=re.I)  # Remove @cappers
    t = re.sub(r'@fast\b', '', t, flags=re.I)
    t = re.sub(r'@wi\b', '', t, flags=re.I)
    t = re.sub(r'@pl\b', '', t, flags=re.I)
    t = re.sub(r'@P\b', '', t, flags=re.I)

    # Remove Discord bot artifacts
    t = re.sub(r'Data Extractor Bot.*?(?=\n|$)', '', t, flags=re.I)
    t = re.sub(r'\bAPP\b\s*—.*?(?=\n|$)', '', t, flags=re.I)
    t = re.sub(r'(?:Yesterday|Today) at \d+:\d+\s*(?:AM|PM)', '', t, flags=re.I)

    # Remove broken/incomplete lines (like "ppers", "ersfree Sfree", "persfree")
    t = re.sub(r'^\s*(?:ppers|ersfree|Sfree|sfree|rstree|cannersfree|Castersfree|persfree)\b.*$', '', t, flags=re.I | re.MULTILINE)
    t = re.sub(r'\bpersfree\b', '', t, flags=re.I)  # Remove persfree anywhere

    # Fix common garbled team names
    t = re.sub(r'\bDodgeppersfree\b', 'Dodgers', t, flags=re.I)
    t = re.sub(r'\b\w*ppersfree\w*\b', '', t, flags=re.I)  # Remove any word containing ppersfree

    # Clean up common noise patterns
    t = t.replace('➡️', ' ').replace('->', ' ').replace('—', '-').replace('–', '-')
    t = re.sub(r'\(\)', '', t)  # Empty parentheses from odds
    t = re.sub(r'\(,\s*\d+:\d+[aep]\)', '', t, flags=re.I)  # Remove (, 6:30e) patterns

    for p in NOISE_PATTERNS:
        t = p.sub(' ', t)

    # Remove standalone @ symbols and cleanup
    t = re.sub(r'\s@\s+', ' ', t)
    t = re.sub(r'^@\s+', '', t, flags=re.MULTILINE)
    t = re.sub(r'@C\b', '', t, flags=re.I)  # Remove @C mentions
    t = re.sub(r'@Do\b', '', t, flags=re.I)

    # Normalize spaces within lines, but preserve line breaks
    t = re.sub(r'[ \t]+', ' ', t)  # spaces and tabs only

    # Clean up multiple newlines and empty lines
    t = re.sub(r'\n\s*\n\s*\n+', '\n\n', t)

    # Remove lines that are just timestamps or single words
    lines = t.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Skip very short lines that look like garbage
        if len(line) < 3 and not re.search(r'\d', line):
            continue
        # Skip lines that are just "Group" or similar
        if line.lower() in ['group', 'bonus', 'exclusive', 'ppers', 'sfree']:
            continue
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines).strip()

def _canonicalize(name: str) -> str:
    key = re.sub(r'\s+', ' ', name).strip().lower()
    return ALIASES.get(key, name)

def _extract_capper(cleaned: str) -> str | None:
    low = cleaned.lower()

    # 1) explicit aliases (longest first to avoid partial hits)
    for alias in sorted(ALIASES.keys(), key=len, reverse=True):
        if alias in low:
            return _canonicalize(ALIASES[alias])

    # 2) known list (case-insensitive)
    for c in sorted(KNOWN_CAPPERS, key=len, reverse=True):
        if c.lower() in low:
            return c

    # 3) handle-style heuristic near the start - but exclude common words
    head_tokens = cleaned.split()[:8]
    for tok in head_tokens:
        token = re.sub(r'[^A-Za-z0-9_]', '', tok)
        if 4 <= len(token) <= 20 and token.lower() not in {
            'dm','free','slate','today','tonight','back','tomorrow','bet','no','picks','vip',
            'play','day','the','wednesday','whale','plays','nfl','sunday','nba','mlb','tonight',
            'cappers','packages','for','with','and','top','opinion','point','matchup','kickoff',
            'nothing','fire','straight','unit','bankroll','like','each','pick'
        }:
            return token
    return None

def _split_lines(cleaned: str):
    # Try to separate probable items by newlines first
    lines = [s.strip() for s in cleaned.split('\n') if s.strip()]
    
    # If multiple lines, return them
    if len(lines) > 1:
        return lines
    
    # Single line - try other separators (but not dash in odds like -110)
    # Split on bullets, multiple spaces, commas, pipes, semicolons
    parts = re.split(r'(?:\s*[•·]\s*|\s{3,}|,(?!\d)|\|(?!\d)|;)', cleaned)
    return [s.strip() for s in parts if s and len(s.strip()) >= 3]

def _looks_like_pick(s: str) -> bool:
    return (
        re.search(r'\b(ML|over|under|spread|total|parlay|teaser|MAXPLAY)\b', s, re.I) or
        re.search(r'[+-]\d{2,4}', s) or
        re.search(r'\d+\.?\d*\s*u\b', s, re.I) or
        re.search(r'\bvs?\b|@|/', s) or
        TEAM_HINT.search(s) is not None or
        re.search(r'\d+\.5', s) or  # spread like +11.5, -2.5
        re.search(r'\b(KBO|MLB|NBA|NFL|NHL|UFC|NCAAB|NCAAF|EPL|UCL)\b', s, re.I) or  # sports leagues
        (re.search(r'\b[A-Z]{2,}\b', s) and re.search(r'[+-]\d', s))  # CAPS team + odds
    )

def _format_pick(s: str) -> str:
    # Clean up the line first
    s = re.sub(r'\(\)', '', s)  # Remove empty parentheses
    s = re.sub(r'\(\s*\)', '', s)  # Remove parentheses with just spaces

    # Extract components
    odds  = re.search(r'([+-]\d{2,4})', s)
    units = re.search(r'(\d+\.?\d*)\s*u\b', s, re.I)
    has_max = re.search(r'\bmax\b', s, re.I)

    # Clean the main text
    clean = re.sub(r'[+-]\d{2,4}', '', s)
    clean = re.sub(r'\d+\.?\d*\s*u\b', '', clean, flags=re.I)
    clean = re.sub(r'\bmax\b', '', clean, flags=re.I)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Build formatted output
    tail = []
    if odds:  tail.append(odds.group(1))
    if units: tail.append(f"{units.group(1)}u{' MAX' if has_max else ''}")
    return clean + ((" " + " ".join(tail)) if tail else "")

def _normalize_no_play(cleaned: str) -> str | None:
    # More specific no-play patterns
    patterns = [
        r'\b(no\s+(bet|play)s?|off\s+day)\b',
        r'\bnothing\s+i\s+like\b',
        r'\bpass\s+(tonight|today)\b',
        r'\bno\s+picks?\b'
    ]
    for pattern in patterns:
        if re.search(pattern, cleaned, re.I):
            return "No official play today — back tomorrow."
    return None

def format_clean_picks(label: str, text: str, ocr_text: str, check_dedup: bool = False) -> str:
    """
    Format picks text for Discord output.
    
    Args:
        label: Channel/source label (for PAID channels)
        text: Raw text content
        ocr_text: OCR-extracted text from images
        check_dedup: If True, check/record dedup hashes (default False for backward compat)
    
    Returns:
        Formatted picks text, or None if message should be skipped (recap/duplicate)
    """
    full = "\n".join([t for t in [text, ocr_text] if t]).strip()
    if not full:
        if label:
            return f"**{label}**\n📸 *[Image]*"
        else:
            return "📸 *[Image]*"

    # Phase 1: Skip recap/results messages
    if is_recap_message(full):
        return None  # Signal to skip this message entirely

    cleaned = _normalize_text(full)
    if not cleaned:
        if label:
            return f"**{label}**\n📸 *[Image content]*"
        else:
            return "📸 *[Image content]*"

    # detect special "no play" messages
    no_play = _normalize_no_play(cleaned)

    capper = _extract_capper(cleaned)
    lines  = _split_lines(cleaned)
    picks  = [_format_pick(x) for x in lines if _looks_like_pick(x)]

    out = []
    # Only add label if it's provided (for PAID channels)
    if label:
        out.append(f"**{label}**")
    if capper:
        out.append(f"**{capper}**")

    if picks:
        out.extend(picks)
    elif no_play:
        out.append(no_play)
    else:
        # For promo-only posts (no picks, just capper name + noise), show image placeholder
        if (len(cleaned) < 50 and capper and 
            re.search(r'(dm|contact|subscribe|join|vip|package|@cappersfree)', cleaned, re.I)):
            out.append("📸 *[Image content]*")
        elif len(cleaned) <= 100:
            out.append(cleaned)
        else:
            out.append("📸 *[Image content]*")

    result = "\n".join(out).strip()
    
    # Phase 2: Content-based deduplication
    if check_dedup and picks:
        pick_text = "\n".join(picks)
        if is_duplicate_pick(capper, pick_text):
            return None  # Skip duplicate
        # Record this pick for future dedup
        record_pick(capper, pick_text)
    
    return result