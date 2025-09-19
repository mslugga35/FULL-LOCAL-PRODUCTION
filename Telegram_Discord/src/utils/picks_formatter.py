# src/utils/picks_formatter.py
import re

# ---- Canonical capper names (your list, cleaned) ----
KNOWN_CAPPERS = [
    "A11 Bets","AMPM","Action Network","AlgoPicks","Analytics Capper","ANON","Bankroll Bill",
    "BeezoWins","Bet Sharper","Blink Bets","BulliesPicks","CashCing","Cblez","Cesar",
    "Cody Covers Spreads","Darth Fader","Dirty Bubble Bets","Dommy Locked","Dormroom Degenerates",
    "DPatt","DuckInvestments","Fern","Glitch Whale","Hammering Hank","Illicit Picks","ISW",
    "Itstroywest","Kims Picks","Kleos","Kingcap","LaFormula","Lear Locks","Match Point Bets",
    "MatthewP07","McBets","MidwestMikeSports","Monumental","Mr Big Bets","Nicky Cashin",
    "NCSharp","Newmark","NRFI Algorithm","Out of Line Bets","PARLAY P","PardonMyPick","PickzHub",
    "Picks 4 Dayzzz","Platinum Locks","PorterPicks","PremPod","ProvenWinner","RBSSportsPlays",
    "Relentless Sports Consulting","RickyPick","Ronald Cabang","SBK (Chips)","Sean Perry Wins",
    "Seeking Returns","Set Point Bets","Sharp Investments","SmartMoneySports","SPS","TBSportsBetting",
    "The Gold Sheet","The Guru","The Gambling Gawd","The Sharp Sheets","This Girl Betz","TMS",
    "Travy","UTAB","VC","Vezino Locks","Vinny","YourDailyCapper","ZachsBets",
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
}

# ---- Noise patterns (headers, promos, separators, emoji spam) ----
NOISE_PATTERNS = [
    re.compile(r'\bCAPPERS?\s*FREE\b.*', re.I),
    re.compile(r'\bFREE\s*(VIP|PICKS?)\b.*', re.I),
    re.compile(r'\b(package|join|subscribe|cheapest|prices?|dm\s*(me)?|contact)\b.*', re.I),
    re.compile(r'DM\s*([➡➜➔→]+|->)?\s*[✅☑️✔️]?\s*@?\w*', re.I),
    re.compile(r'@cappersfree', re.I),
    re.compile(r'^\d{1,2}:\d{2}\s*(am|pm)?$', re.I),
    re.compile(r'[➖─—\-=._•*|·]{3,}'),  # long separators
    re.compile(r'[\u2705\u26A0\u2757\u26D4\u274C]'),  # ✅⚠️❗⛔❌
    re.compile(r'\bstake\.com\b', re.I),
    re.compile(r'Browse\s+Casino', re.I),
    re.compile(r'Bet\s+Slip', re.I),
    re.compile(r'Sports\s+Chat', re.I),
    re.compile(r'View\s+All.*', re.I),
]

TEAM_HINT = re.compile(
    r'\b(Lakers|Warriors|Yankees|Dodgers|Patriots|Chiefs|Arsenal|Real\s*Madrid|Barcelona|PSG|Celtics|Knicks|Braves|Cowboys|Dolphins|Bills|Marlins|Twins|Athletics|Royals)\b',
    re.I
)

def _normalize_text(t: str) -> str:
    if not t: return ""
    t = t.replace('➡️', ' ').replace('->', ' ').replace('—', '-').replace('–', '-')
    # split repeated "CAPPERS FREE" blocks by keeping content, dropping headers
    t = re.sub(r'(?:^|\n)\s*CAPPERS?\s*FREE[^\n]*\n+', '\n', t, flags=re.I)
    for p in NOISE_PATTERNS:
        t = p.sub(' ', t)
    # Remove standalone @ symbols
    t = re.sub(r'\s@\s+', ' ', t)
    t = re.sub(r'^@\s+', '', t)
    # Normalize spaces within lines, but preserve line breaks
    t = re.sub(r'[ \t]+', ' ', t)  # spaces and tabs only
    return t.strip()

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
        re.search(r'\b(ML|over|under|spread|total|parlay|teaser)\b', s, re.I) or
        re.search(r'[+-]\d{2,4}', s) or
        re.search(r'\d+\.?\d*\s*u\b', s, re.I) or
        re.search(r'\bvs?\b|@|/', s) or
        TEAM_HINT.search(s) is not None or
        re.search(r'\d+\.5', s)  # spread like +11.5, -2.5
    )

def _format_pick(s: str) -> str:
    odds  = re.search(r'([+-]\d{2,4})', s)
    units = re.search(r'(\d+\.?\d*)\s*u\b', s, re.I)
    has_max = re.search(r'\bmax\b', s, re.I)

    clean = re.sub(r'[+-]\d{2,4}', '', s)
    clean = re.sub(r'\d+\.?\d*\s*u\b', '', clean, flags=re.I)
    clean = re.sub(r'\bmax\b', '', clean, flags=re.I)
    clean = re.sub(r'\s+', ' ', clean).strip()

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
        return f"**{label}**\n📸 *[Image]*"

    cleaned = _normalize_text(full)
    if not cleaned:
        return f"**{label}**\n📸 *[Image content]*"

    # detect special "no play" messages
    no_play = _normalize_no_play(cleaned)

    capper = _extract_capper(cleaned)
    lines  = _split_lines(cleaned)
    picks  = [_format_pick(x) for x in lines if _looks_like_pick(x)]

    out = [f"**{label}**"]
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