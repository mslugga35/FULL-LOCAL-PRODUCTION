import re

# ---- Canonical capper names ----
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

# ---- Alias mappings ----
ALIASES = {
    "cblez": "Cblez",
    "cblez.": "Cblez", 
    "nickycashin": "Nicky Cashin",
    "platinumlocks": "Platinum Locks",
    "cabang": "Ronald Cabang",
    "sbk": "SBK (Chips)",
    "yourdailycapper": "YourDailyCapper",
    "ncsharp": "NCSharp",
    "thb": "THB OCR",
    "vegasclub": "VegasClub",
    "vegasmira": "vegasmirabet",
    "vegas_mira_bet": "vegasmirabet",
}

# ---- Noise patterns ----
NOISE_PATTERNS = [
    re.compile(r'\bCAPPERS?\s*FREE\b.*', re.I),
    re.compile(r'\bFREE\s*(VIP|PICKS?)\b.*', re.I),
    re.compile(r'DM\s*([➡➜➔→]+|->)?\s*.*@?\w*', re.I),
    re.compile(r'@cappersfree', re.I),
    re.compile(r'[➖─—\-=._•*|·]{3,}'),
    re.compile(r'\b(package|join|subscribe|cheapest|prices?|contact)\b', re.I),
]

def _clean_text(text: str) -> str:
    if not text: return ""
    # Remove noise patterns
    for pattern in NOISE_PATTERNS:
        text = pattern.sub(' ', text)
    # Clean whitespace
    return re.sub(r'\s+', ' ', text).strip()

def _extract_capper(text: str) -> str:
    text_lower = text.lower()
    
    # Check aliases first
    for alias, canonical in ALIASES.items():
        if alias in text_lower:
            return canonical
    
    # Check known cappers
    for capper in sorted(KNOWN_CAPPERS, key=len, reverse=True):
        if capper.lower() in text_lower:
            return capper
    
    return None

def _extract_picks(text: str):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    picks = []
    
    for line in lines:
        # Skip if looks like header/promo
        if any(word in line.lower() for word in ['free', 'dm', 'vip', 'subscribe']):
            continue
            
        # Check if looks like a pick
        has_bet_terms = re.search(r'\b(ML|over|under|spread|total|parlay)\b', line, re.I)
        has_odds = re.search(r'[+-]\d{2,4}', line) 
        has_units = re.search(r'\d+\.?\d*\s*u\b', line, re.I)
        has_vs = re.search(r'\w+\s+(vs?|@|/)\s+\w+', line, re.I)
        has_team = re.search(r'\b(Lakers|Warriors|Yankees|Dodgers|Patriots|Chiefs|Braves|Cowboys)\b', line, re.I)
        
        if has_bet_terms or has_odds or has_units or has_vs or has_team:
            picks.append(line)
    
    return picks

def _check_no_play(text: str) -> bool:
    return re.search(r'\b(no\s+(bet|play)|off\s+day|nothing.*like|pass\s+(tonight|today))\b', text, re.I) is not None

def format_clean_picks(label: str, text: str, ocr_text: str) -> str:
    full_text = "\n".join([t for t in [text, ocr_text] if t]).strip()
    if not full_text:
        return f"**{label}**\n📸 *[Image]*"
    
    cleaned = _clean_text(full_text)
    if not cleaned:
        return f"**{label}**\n📸 *[Image content]*"
    
    # Check for no-play message
    if _check_no_play(cleaned):
        capper = _extract_capper(cleaned)
        out = [f"**{label}**"]
        if capper:
            out.append(f"**{capper}**")
        out.append("No official play today — back tomorrow.")
        return "\n".join(out)
    
    # Extract capper and picks
    capper = _extract_capper(cleaned)
    picks = _extract_picks(cleaned)
    
    out = [f"**{label}**"]
    if capper:
        out.append(f"**{capper}**")
    
    if picks:
        out.extend(picks)
    else:
        out.append(cleaned if len(cleaned) <= 200 else "📸 *[Image content]*")
    
    return "\n".join(out)

# TEST CASES
if __name__ == "__main__":
    test_cases = [
        ("YourDailyCapper test", "CAPPERS FREE\n@YourDailyCapper DM for VIP\nMLB: Brewers -1.5 (+110) 2u\nNBA: Warriors ML -145 1.5u"),
        ("Travy test", "Travy\nBraves ML (1U)\nPadres -1.5\nWhite Sox ML"),
        ("vegasmira alias test", "vegasmira\nTwins ML 1u\nKansas St ML 1u\nAthletics ML 1u"),
        ("No play test", "CBLEZ.\nNo bet tonight - back tomorrow with slate"),
        ("DuckInvestments test", "DuckInvestments\nNew Mexico TT Over 18.5\nNew Mexico +15.5\nColgate +38.5"),
    ]
    
    print("=== TESTING FIXED FORMATTER ===")
    for name, test in test_cases:
        print(f"\n--- {name} ---")
        print("INPUT:")
        print(test)
        result = format_clean_picks("free_cappers", "", test)
        print("\nOUTPUT:")
        print(result)
        print("-" * 50)