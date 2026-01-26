# src/utils/picks_formatter.py
import re

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
    re.compile(r'[\u2705\u26A0\u2757\u26D4\u274C]'),  # ✅⚠️❗⛔❌
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

def format_clean_picks(label: str, text: str, ocr_text: str) -> str:
    full = "\n".join([t for t in [text, ocr_text] if t]).strip()
    if not full:
        if label:
            return f"**{label}**\n📸 *[Image]*"
        else:
            return "📸 *[Image]*"

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

    return "\n".join(out).strip()