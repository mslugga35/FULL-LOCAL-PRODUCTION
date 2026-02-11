"""
Team name normalization mappings
Maps all variations of team names to canonical short codes
"""

# NBA Teams
NBA_TEAMS = {
    "ATL": ["Hawks", "Atlanta Hawks", "Atlanta", "ATL Hawks"],
    "BOS": ["Celtics", "Boston Celtics", "Boston", "BOS Celtics"],
    "BKN": ["Nets", "Brooklyn Nets", "Brooklyn", "BKN Nets", "New Jersey Nets"],
    "CHA": ["Hornets", "Charlotte Hornets", "Charlotte", "CHA Hornets"],
    "CHI": ["Bulls", "Chicago Bulls", "Chicago", "CHI Bulls"],
    "CLE": ["Cavaliers", "Cleveland Cavaliers", "Cleveland", "CLE Cavaliers", "Cavs"],
    "DAL": ["Mavericks", "Dallas Mavericks", "Dallas", "DAL Mavericks", "Mavs"],
    "DEN": ["Nuggets", "Denver Nuggets", "Denver", "DEN Nuggets"],
    "DET": ["Pistons", "Detroit Pistons", "Detroit", "DET Pistons"],
    "GSW": ["Warriors", "Golden State Warriors", "Golden State", "GSW Warriors", "GS Warriors", "GS"],
    "HOU": ["Rockets", "Houston Rockets", "Houston", "HOU Rockets"],
    "IND": ["Pacers", "Indiana Pacers", "Indiana", "IND Pacers"],
    "LAC": ["Clippers", "Los Angeles Clippers", "LA Clippers", "LAC Clippers", "L.A. Clippers"],
    "LAL": ["Lakers", "Los Angeles Lakers", "LA Lakers", "LAL Lakers", "L.A. Lakers"],
    "MEM": ["Grizzlies", "Memphis Grizzlies", "Memphis", "MEM Grizzlies"],
    "MIA": ["Heat", "Miami Heat", "Miami", "MIA Heat"],
    "MIL": ["Bucks", "Milwaukee Bucks", "Milwaukee", "MIL Bucks"],
    "MIN": ["Timberwolves", "Minnesota Timberwolves", "Minnesota", "MIN Timberwolves", "Wolves", "T-Wolves"],
    "NOP": ["Pelicans", "New Orleans Pelicans", "New Orleans", "NOP Pelicans", "NO Pelicans"],
    "NYK": ["Knicks", "New York Knicks", "New York", "NYK Knicks", "NY Knicks"],
    "OKC": ["Thunder", "Oklahoma City Thunder", "Oklahoma City", "OKC Thunder"],
    "ORL": ["Magic", "Orlando Magic", "Orlando", "ORL Magic"],
    "PHI": ["76ers", "Philadelphia 76ers", "Philadelphia", "PHI 76ers", "Sixers", "Philly"],
    "PHX": ["Suns", "Phoenix Suns", "Phoenix", "PHX Suns"],
    "POR": ["Trail Blazers", "Portland Trail Blazers", "Portland", "POR Trail Blazers", "Blazers"],
    "SAC": ["Kings", "Sacramento Kings", "Sacramento", "SAC Kings"],
    "SAS": ["Spurs", "San Antonio Spurs", "San Antonio", "SAS Spurs", "SA Spurs"],
    "TOR": ["Raptors", "Toronto Raptors", "Toronto", "TOR Raptors"],
    "UTA": ["Jazz", "Utah Jazz", "Utah", "UTA Jazz"],
    "WAS": ["Wizards", "Washington Wizards", "Washington", "WAS Wizards"],
}

# NFL Teams
NFL_TEAMS = {
    "ARI": ["Cardinals", "Arizona Cardinals", "Arizona"],
    "ATL": ["Falcons", "Atlanta Falcons", "Atlanta"],
    "BAL": ["Ravens", "Baltimore Ravens", "Baltimore"],
    "BUF": ["Bills", "Buffalo Bills", "Buffalo"],
    "CAR": ["Panthers", "Carolina Panthers", "Carolina"],
    "CHI": ["Bears", "Chicago Bears", "Chicago"],
    "CIN": ["Bengals", "Cincinnati Bengals", "Cincinnati"],
    "CLE": ["Browns", "Cleveland Browns", "Cleveland"],
    "DAL": ["Cowboys", "Dallas Cowboys", "Dallas"],
    "DEN": ["Broncos", "Denver Broncos", "Denver"],
    "DET": ["Lions", "Detroit Lions", "Detroit"],
    "GB": ["Packers", "Green Bay Packers", "Green Bay", "GNB"],
    "HOU": ["Texans", "Houston Texans", "Houston"],
    "IND": ["Colts", "Indianapolis Colts", "Indianapolis"],
    "JAX": ["Jaguars", "Jacksonville Jaguars", "Jacksonville"],
    "KC": ["Chiefs", "Kansas City Chiefs", "Kansas City"],
    "LV": ["Raiders", "Las Vegas Raiders", "Las Vegas", "Oakland Raiders", "OAK"],
    "LAC": ["Chargers", "Los Angeles Chargers", "LA Chargers", "San Diego Chargers"],
    "LAR": ["Rams", "Los Angeles Rams", "LA Rams", "St. Louis Rams"],
    "MIA": ["Dolphins", "Miami Dolphins", "Miami"],
    "MIN": ["Vikings", "Minnesota Vikings", "Minnesota"],
    "NE": ["Patriots", "New England Patriots", "New England", "Pats"],
    "NO": ["Saints", "New Orleans Saints", "New Orleans"],
    "NYG": ["Giants", "New York Giants", "NY Giants"],
    "NYJ": ["Jets", "New York Jets", "NY Jets"],
    "PHI": ["Eagles", "Philadelphia Eagles", "Philadelphia", "Philly"],
    "PIT": ["Steelers", "Pittsburgh Steelers", "Pittsburgh"],
    "SF": ["49ers", "San Francisco 49ers", "San Francisco", "Niners"],
    "SEA": ["Seahawks", "Seattle Seahawks", "Seattle"],
    "TB": ["Buccaneers", "Tampa Bay Buccaneers", "Tampa Bay", "Bucs"],
    "TEN": ["Titans", "Tennessee Titans", "Tennessee"],
    "WAS": ["Commanders", "Washington Commanders", "Washington", "Football Team", "Redskins"],
}

# NHL Teams
NHL_TEAMS = {
    "ANA": ["Ducks", "Anaheim Ducks", "Anaheim"],
    "ARI": ["Coyotes", "Arizona Coyotes", "Arizona", "Utah Hockey Club", "Utah HC"],
    "BOS": ["Bruins", "Boston Bruins", "Boston"],
    "BUF": ["Sabres", "Buffalo Sabres", "Buffalo"],
    "CGY": ["Flames", "Calgary Flames", "Calgary"],
    "CAR": ["Hurricanes", "Carolina Hurricanes", "Carolina", "Canes"],
    "CHI": ["Blackhawks", "Chicago Blackhawks", "Chicago"],
    "COL": ["Avalanche", "Colorado Avalanche", "Colorado", "Avs"],
    "CBJ": ["Blue Jackets", "Columbus Blue Jackets", "Columbus"],
    "DAL": ["Stars", "Dallas Stars", "Dallas"],
    "DET": ["Red Wings", "Detroit Red Wings", "Detroit"],
    "EDM": ["Oilers", "Edmonton Oilers", "Edmonton"],
    "FLA": ["Panthers", "Florida Panthers", "Florida"],
    "LAK": ["Kings", "Los Angeles Kings", "LA Kings"],
    "MIN": ["Wild", "Minnesota Wild", "Minnesota"],
    "MTL": ["Canadiens", "Montreal Canadiens", "Montreal", "Habs"],
    "NSH": ["Predators", "Nashville Predators", "Nashville", "Preds"],
    "NJD": ["Devils", "New Jersey Devils", "New Jersey"],
    "NYI": ["Islanders", "New York Islanders", "NY Islanders"],
    "NYR": ["Rangers", "New York Rangers", "NY Rangers"],
    "OTT": ["Senators", "Ottawa Senators", "Ottawa", "Sens"],
    "PHI": ["Flyers", "Philadelphia Flyers", "Philadelphia"],
    "PIT": ["Penguins", "Pittsburgh Penguins", "Pittsburgh", "Pens"],
    "SJS": ["Sharks", "San Jose Sharks", "San Jose"],
    "SEA": ["Kraken", "Seattle Kraken", "Seattle"],
    "STL": ["Blues", "St. Louis Blues", "St Louis Blues", "St. Louis"],
    "TBL": ["Lightning", "Tampa Bay Lightning", "Tampa Bay", "Tampa"],
    "TOR": ["Maple Leafs", "Toronto Maple Leafs", "Toronto", "Leafs"],
    "VAN": ["Canucks", "Vancouver Canucks", "Vancouver"],
    "VGK": ["Golden Knights", "Vegas Golden Knights", "Vegas", "VGK"],
    "WPG": ["Jets", "Winnipeg Jets", "Winnipeg"],
    "WSH": ["Capitals", "Washington Capitals", "Washington", "Caps"],
}

# MLB Teams
MLB_TEAMS = {
    "ARI": ["Diamondbacks", "Arizona Diamondbacks", "Arizona", "D-backs"],
    "ATL": ["Braves", "Atlanta Braves", "Atlanta"],
    "BAL": ["Orioles", "Baltimore Orioles", "Baltimore", "O's"],
    "BOS": ["Red Sox", "Boston Red Sox", "Boston"],
    "CHC": ["Cubs", "Chicago Cubs", "Chi Cubs"],
    "CHW": ["White Sox", "Chicago White Sox", "Chi White Sox", "CWS"],
    "CIN": ["Reds", "Cincinnati Reds", "Cincinnati"],
    "CLE": ["Guardians", "Cleveland Guardians", "Cleveland", "Indians"],
    "COL": ["Rockies", "Colorado Rockies", "Colorado"],
    "DET": ["Tigers", "Detroit Tigers", "Detroit"],
    "HOU": ["Astros", "Houston Astros", "Houston"],
    "KC": ["Royals", "Kansas City Royals", "Kansas City"],
    "LAA": ["Angels", "Los Angeles Angels", "LA Angels", "Anaheim Angels"],
    "LAD": ["Dodgers", "Los Angeles Dodgers", "LA Dodgers"],
    "MIA": ["Marlins", "Miami Marlins", "Miami", "Florida Marlins"],
    "MIL": ["Brewers", "Milwaukee Brewers", "Milwaukee"],
    "MIN": ["Twins", "Minnesota Twins", "Minnesota"],
    "NYM": ["Mets", "New York Mets", "NY Mets"],
    "NYY": ["Yankees", "New York Yankees", "NY Yankees"],
    "OAK": ["Athletics", "Oakland Athletics", "Oakland", "A's"],
    "PHI": ["Phillies", "Philadelphia Phillies", "Philadelphia"],
    "PIT": ["Pirates", "Pittsburgh Pirates", "Pittsburgh"],
    "SD": ["Padres", "San Diego Padres", "San Diego"],
    "SF": ["Giants", "San Francisco Giants", "San Francisco"],
    "SEA": ["Mariners", "Seattle Mariners", "Seattle", "M's"],
    "STL": ["Cardinals", "St. Louis Cardinals", "St Louis Cardinals", "St. Louis"],
    "TB": ["Rays", "Tampa Bay Rays", "Tampa Bay", "Tampa"],
    "TEX": ["Rangers", "Texas Rangers", "Texas"],
    "TOR": ["Blue Jays", "Toronto Blue Jays", "Toronto", "Jays"],
    "WAS": ["Nationals", "Washington Nationals", "Washington", "Nats"],
}

# NCAAB - Top 100 programs (add more as needed)
NCAAB_TEAMS = {
    "DUKE": ["Duke", "Duke Blue Devils", "Blue Devils"],
    "UNC": ["North Carolina", "UNC", "Tar Heels", "NC Tar Heels"],
    "KANSAS": ["Kansas", "Kansas Jayhawks", "Jayhawks", "KU"],
    "KENTUCKY": ["Kentucky", "Kentucky Wildcats", "UK Wildcats", "UK"],
    "GONZAGA": ["Gonzaga", "Gonzaga Bulldogs", "Zags"],
    "ARIZONA": ["Arizona", "Arizona Wildcats"],
    "UCLA": ["UCLA", "UCLA Bruins", "Bruins"],
    "PURDUE": ["Purdue", "Purdue Boilermakers", "Boilermakers"],
    "HOUSTON": ["Houston", "Houston Cougars", "UH"],
    "AUBURN": ["Auburn", "Auburn Tigers"],
    "ALABAMA": ["Alabama", "Alabama Crimson Tide", "Bama"],
    "TENNESSEE": ["Tennessee", "Tennessee Volunteers", "Vols"],
    "MICHIGAN": ["Michigan", "Michigan Wolverines", "Wolverines"],
    "MICHIGAN ST": ["Michigan State", "Michigan St", "MSU", "Spartans"],
    "OHIO ST": ["Ohio State", "Ohio St", "OSU", "Buckeyes"],
    "LOUISVILLE": ["Louisville", "Louisville Cardinals"],
    "INDIANA": ["Indiana", "Indiana Hoosiers", "Hoosiers", "IU"],
    "SYRACUSE": ["Syracuse", "Syracuse Orange", "Cuse"],
    "UCONN": ["Connecticut", "UConn", "Huskies"],
    "VILLANOVA": ["Villanova", "Villanova Wildcats", "Nova"],
    "FLORIDA": ["Florida", "Florida Gators", "Gators", "UF"],
    "BAYLOR": ["Baylor", "Baylor Bears"],
    "IOWA": ["Iowa", "Iowa Hawkeyes", "Hawkeyes"],
    "IOWA ST": ["Iowa State", "Iowa St", "Cyclones"],
    "KANSAS ST": ["Kansas State", "Kansas St", "K-State", "Wildcats"],
    "TEXAS": ["Texas", "Texas Longhorns", "Longhorns"],
    "TEXAS TECH": ["Texas Tech", "Red Raiders"],
    "TCU": ["TCU", "TCU Horned Frogs", "Horned Frogs"],
    "MEMPHIS": ["Memphis", "Memphis Tigers"],
    "XAVIER": ["Xavier", "Xavier Musketeers"],
    "CREIGHTON": ["Creighton", "Creighton Bluejays", "Bluejays"],
    "MARQUETTE": ["Marquette", "Marquette Golden Eagles", "Golden Eagles"],
    "PROVIDENCE": ["Providence", "Providence Friars", "Friars"],
    "ARKANSAS": ["Arkansas", "Arkansas Razorbacks", "Razorbacks"],
    "LSU": ["LSU", "Louisiana State", "Tigers"],
    "GEORGIA": ["Georgia", "Georgia Bulldogs", "UGA"],
    "SOUTH CAROLINA": ["South Carolina", "Gamecocks"],
    "CLEMSON": ["Clemson", "Clemson Tigers"],
    "NC STATE": ["NC State", "North Carolina State", "Wolfpack"],
    "VIRGINIA": ["Virginia", "Virginia Cavaliers", "Cavaliers", "UVA"],
    "VIRGINIA TECH": ["Virginia Tech", "Hokies", "VT"],
    "WAKE FOREST": ["Wake Forest", "Demon Deacons", "Wake"],
    "PITTSBURGH": ["Pittsburgh", "Pitt", "Panthers"],
    "NOTRE DAME": ["Notre Dame", "Fighting Irish", "ND"],
    "WISCONSIN": ["Wisconsin", "Wisconsin Badgers", "Badgers"],
    "ILLINOIS": ["Illinois", "Fighting Illini", "Illini"],
    "NORTHWESTERN": ["Northwestern", "Wildcats"],
    "PENN ST": ["Penn State", "Penn St", "Nittany Lions", "PSU"],
    "MARYLAND": ["Maryland", "Terrapins", "Terps"],
    "RUTGERS": ["Rutgers", "Scarlet Knights"],
    "OREGON": ["Oregon", "Oregon Ducks", "Ducks"],
    "WASHINGTON": ["Washington", "Washington Huskies", "UW"],
    "COLORADO": ["Colorado", "Colorado Buffaloes", "Buffs", "CU"],
    "UTAH": ["Utah", "Utah Utes", "Utes"],
    "ARIZONA ST": ["Arizona State", "Arizona St", "Sun Devils", "ASU"],
    "USC": ["USC", "Southern California", "Trojans"],
    "STANFORD": ["Stanford", "Stanford Cardinal", "Cardinal"],
    "CAL": ["California", "Cal", "Golden Bears", "Cal Bears"],
}

# NCAAF - Power conferences + notable programs
NCAAF_TEAMS = {
    **{k: v for k, v in NCAAB_TEAMS.items()},  # Reuse college names
    "GEORGIA": ["Georgia", "Georgia Bulldogs", "UGA", "Dawgs"],
    "OHIO ST": ["Ohio State", "Ohio St", "OSU", "Buckeyes"],
    "MICHIGAN": ["Michigan", "Michigan Wolverines", "Wolverines", "UM"],
    "ALABAMA": ["Alabama", "Alabama Crimson Tide", "Bama", "Tide"],
    "CLEMSON": ["Clemson", "Clemson Tigers", "Tigers"],
    "NOTRE DAME": ["Notre Dame", "Fighting Irish", "ND"],
    "PENN ST": ["Penn State", "Penn St", "Nittany Lions", "PSU"],
    "TEXAS": ["Texas", "Texas Longhorns", "Longhorns", "UT"],
    "OKLAHOMA": ["Oklahoma", "Oklahoma Sooners", "Sooners", "OU"],
    "USC": ["USC", "Southern California", "Trojans"],
    "OREGON": ["Oregon", "Oregon Ducks", "Ducks"],
    "FLORIDA ST": ["Florida State", "Florida St", "Seminoles", "FSU", "Noles"],
    "MIAMI": ["Miami", "Miami Hurricanes", "Hurricanes", "The U"],
    "LSU": ["LSU", "Louisiana State", "Tigers", "Geaux Tigers"],
}

# Combine all leagues for lookup
ALL_TEAMS = {
    "NBA": NBA_TEAMS,
    "NFL": NFL_TEAMS,
    "NHL": NHL_TEAMS,
    "MLB": MLB_TEAMS,
    "NCAAB": NCAAB_TEAMS,
    "NCAAF": NCAAF_TEAMS,
    "CBB": NCAAB_TEAMS,  # Alias
    "CFB": NCAAF_TEAMS,  # Alias
}


def normalize_team(raw_name: str, sport: str = None) -> tuple:
    """
    Normalize a team name to its canonical short code.
    
    Args:
        raw_name: Raw team name (e.g., "Lakers", "Los Angeles Lakers", "LAL")
        sport: Optional sport to narrow search (NBA, NFL, etc.)
    
    Returns:
        Tuple of (canonical_code, sport) or (original_name, None) if not found
    """
    if not raw_name:
        return (raw_name, None)
    
    raw_lower = raw_name.lower().strip()
    
    # If sport specified, search only that league
    if sport and sport.upper() in ALL_TEAMS:
        teams = ALL_TEAMS[sport.upper()]
        for code, aliases in teams.items():
            if raw_lower == code.lower():
                return (code, sport.upper())
            for alias in aliases:
                if raw_lower == alias.lower():
                    return (code, sport.upper())
    
    # Search all leagues
    for league, teams in ALL_TEAMS.items():
        for code, aliases in teams.items():
            if raw_lower == code.lower():
                return (code, league)
            for alias in aliases:
                if raw_lower == alias.lower():
                    return (code, league)
    
    # Not found - return original
    return (raw_name, None)


def get_team_display_name(code: str, sport: str) -> str:
    """Get the display name for a team code."""
    if sport and sport.upper() in ALL_TEAMS:
        teams = ALL_TEAMS[sport.upper()]
        if code in teams:
            # Return first alias (usually the short name like "Lakers")
            return teams[code][0]
    return code
