# TEST VERSION - NEW FORMATTER
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
    r'\b(Lakers|Warriors|Yankees|Dodgers|Patriots|Chiefs|Arsenal|Real\s*Madrid|Barcelona|PSG|Celtics|Knicks|Braves|Cowboys)\b',
    re.I
)

def _normalize_text(t: str) -> str:
    if not t: return ""
    t = t.replace('➡️', ' ').replace('->', ' ').replace('—', '-').replace('–', '-')
    # split repeated "CAPPERS FREE" blocks by keeping content, dropping headers
    t = re.sub(r'(?:^|\n)\s*CAPPERS?\s*FREE[^\n]*\n+', '\n', t, flags=re.I)
    for p in NOISE_PATTERNS:
        t = p.sub(' ', t)
    return re.sub(r'\s+', ' ', t).strip()

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

    # 3) handle-style heuristic near the start
    head_tokens = cleaned.split()[:10]
    for tok in head_tokens:
        token = re.sub(r'[^A-Za-z0-9_]', '', tok)
        if 3 <= len(token) <= 24 and token.lower() not in {
            'dm','free','slate','today','tonight','back','tomorrow','bet','no','picks','vip'
        }:
            return _canonicalize(token)
    return None

def _split_lines(cleaned: str):
    # try to separate probable items
    parts = re.split(r'(?:\s*[•·\-–—]\s*|\s{2,}|,|\||;|\n)', cleaned)
    return [s.strip() for s in parts if s and len(s.strip()) >= 3]

def _looks_like_pick(s: str) -> bool:
    return (
        re.search(r'\b(ML|over|under|spread|total|parlay)\b', s, re.I) or
        re.search(r'[+-]\d{2,4}', s) or
        re.search(r'\d+\.?\d*\s*u\b', s, re.I) or
        re.search(r'\bvs?\b|@|/', s) or
        TEAM_HINT.search(s) is not None
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
    if re.search(r'\b(no\s+(bet|play)|off\s+day|nothing\s+i\s+like|pass\s+(tonight|today))\b', cleaned, re.I):
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
        # small clean note fallback (avoid promo spam)
        out.append(cleaned if len(cleaned) <= 200 else "📸 *[Image content]*")

    return "\n".join(out).strip()

# TEST CASES
if __name__ == "__main__":
    test_cases = [
        "CAPPERS FREE 💥\n@YourDailyCapper ✅✅ DM➡️ for VIP\nMLB: Brewers -1.5 (+110) 2u\nNBA: Warriors ML -145 1.5u",
        "Travy\nBraves ML (1U)\nFriday Premium Plays\nPadres -1.5\nBraves ML\nWhite Sox ML",
        "vegasmira\nTwins ML 1u\nKansas St ML 1u\nAthletics ML 1u",
        "CBLEZ.\nNo bet tonight - back tomorrow with slate",
        "DuckInvestments\nNew Mexico TT Over 18.5\nNew Mexico +15.5\nColgate +38.5",
    ]
    
    print("=== TESTING NEW FORMATTER ===")
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print("INPUT:", repr(test))
        result = format_clean_picks("free_cappers", "", test)
        print("OUTPUT:")
        print(result)
        print()