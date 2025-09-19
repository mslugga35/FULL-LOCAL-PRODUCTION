/**
 * AI Pick Formatter for Hetzner - Complete Port from Local Implementation
 * Includes all sophisticated text cleaning and smart pick parsing
 * Designed to work with Google Vision API for 90%+ accuracy
 */

// Known cappers from your whitelist (extended)
const KNOWN_CAPPERS = [
  // Original list
  'Cblez', 'NickyCashin', 'AFS', 'ISW', 'VC', 'PorterPicks', 'SmartMoneySports', 'Q9',
  'yourdailycapper', 'Max play', 'BulliesPicks', 'PlatinumLocks', 'BankrollBill',
  'ZachsBets', 'NcSharp', 'NCSharp', 'THB OCR', 'VegasClub', 'FreeBet', 'VIP',
  // Paid cappers
  'UTAB', 'Diamond', 'Chamba', 'UATB',
  // Additional common cappers
  'SharpBets', 'ProPicks', 'ElitePicks', 'GoldPicks', 'PremiumBets',
  'WinningPicks', 'TopShelf', 'MoneyMaker', 'BetGuru', 'PickMaster'
];

// Comprehensive noise patterns to remove
const NOISE_PATTERNS = [
  // Social media handles
  /@cappersfree/gi,
  /DM\s*➡?.*@cappersfree/gi,
  /DM\s*➡?\s*@\w+/gi,
  /@everyone/gi,
  /@here/gi,

  // Promotional text
  /^follow|^subscribe|^join/i,
  /^like\s+and\s+share/i,
  /^retweet/i,
  /click\s+here/i,
  /link\s+in\s+bio/i,

  // Time stamps
  /^\d{1,2}:\d{2}\s*(am|pm)?$/i,
  /^\d{1,2}\/\d{1,2}\/\d{2,4}$/,

  // Separators
  /^[➖\-–—_=•*| .]{3,}$/,
  /^[\*]{3,}$/,
  /^[\.]{3,}$/,

  // Casino/gambling site noise
  /stake\.com/gi,
  /Browse Casino/gi,
  /Bet Slip/gi,
  /Sports Chat/gi,
  /draftkings/gi,
  /fanduel/gi,
  /betmgm/gi,

  // UI elements
  /^back$/i,
  /^menu$/i,
  /^home$/i,
  /^settings$/i,
  /^logout$/i,
  /^refresh$/i,

  // Discord/Telegram specific
  /^pinned message/i,
  /^edited$/i,
  /typing\.\.\./i,
  /^online$/i,
  /^offline$/i,

  // Common OCR artifacts
  /^[^a-zA-Z0-9\s]{5,}$/,  // Lines with mostly special characters
  /^.{1,2}$/,              // Very short lines (1-2 chars)
  /^\s+$/                  // Empty lines
];

// Sport identifiers
const SPORTS_MAP = {
  'MLB': ['baseball', 'mlb', 'yankees', 'dodgers', 'astros', 'red sox', 'mets'],
  'NBA': ['basketball', 'nba', 'lakers', 'warriors', 'celtics', 'heat', 'nets'],
  'NFL': ['football', 'nfl', 'patriots', 'chiefs', 'cowboys', 'packers', 'bills'],
  'NHL': ['hockey', 'nhl', 'rangers', 'bruins', 'lightning', 'avalanche'],
  'UFC': ['ufc', 'mma', 'fight', 'boxing'],
  'NCAAB': ['ncaab', 'college basketball', 'march madness'],
  'NCAAF': ['ncaaf', 'college football', 'cfb'],
  'Soccer': ['soccer', 'football', 'premier league', 'champions league', 'la liga', 'serie a'],
  'Tennis': ['tennis', 'atp', 'wta', 'wimbledon', 'us open'],
  'Golf': ['golf', 'pga', 'masters', 'lpga']
};

// Bet type patterns
const BET_PATTERNS = {
  moneyline: /\b(ML|moneyline|money line|to win)\b/i,
  spread: /\b(spread|points?|\+\d+\.5|-\d+\.5|ATS)\b/i,
  total: /\b(over|under|O\/U|total|ov|un)\b/i,
  parlay: /\b(parlay|combo|multi|accumulator)\b/i,
  prop: /\b(prop|props?|player props?|first)\b/i,
  futures: /\b(futures?|to win|championship|MVP)\b/i
};

/**
 * Deep clean OCR text with multi-stage processing
 */
function deepCleanText(text) {
  if (!text) return '';

  // Stage 1: Basic cleanup
  let cleaned = text;

  // Remove noise patterns
  for (const pattern of NOISE_PATTERNS) {
    cleaned = cleaned.replace(pattern, '');
  }

  // Stage 2: Fix common OCR errors
  cleaned = cleaned
    // Fix common letter/number confusion
    .replace(/\bl\b/g, '1')           // Standalone 'l' is probably '1'
    .replace(/\bO\b/g, '0')           // Standalone 'O' is probably '0'
    .replace(/\bi\b(?=\d)/g, '1')    // 'i' before numbers is probably '1'

    // Fix spacing issues
    .replace(/([a-z])([A-Z])/g, '$1 $2')  // Add space between camelCase
    .replace(/(\d)([A-Z])/g, '$1 $2')     // Add space between number and capital
    .replace(/([A-Z]{2,})([A-Z][a-z])/g, '$1 $2')  // Split consecutive caps

    // Fix common betting terms
    .replace(/\bov\b/gi, 'over')
    .replace(/\bun\b/gi, 'under')
    .replace(/\bu\b/gi, 'units')
    .replace(/\bpts?\b/gi, 'points')

    // Normalize odds format
    .replace(/\+\s+(\d{3,4})/g, '+$1')
    .replace(/\-\s+(\d{3,4})/g, '-$1')

    // Fix decimal odds
    .replace(/(\d)\s*\.\s*(\d)/g, '$1.$2')

    // Remove excessive whitespace
    .replace(/\s+/g, ' ')
    .replace(/^\s+|\s+$/g, '');

  // Stage 3: Line-by-line processing
  const lines = cleaned.split('\n');
  const processedLines = [];

  for (let line of lines) {
    line = line.trim();

    // Skip empty or noise lines
    if (line.length < 3) continue;
    if (NOISE_PATTERNS.some(pattern => pattern.test(line))) continue;

    // Keep lines with betting content
    const hasBettingContent =
      BET_PATTERNS.moneyline.test(line) ||
      BET_PATTERNS.spread.test(line) ||
      BET_PATTERNS.total.test(line) ||
      /[+-]\d{3,4}/.test(line) ||      // Has odds
      /\d+\.?\d*\s*u/i.test(line) ||   // Has units
      /\w+\s+(vs?|@|\/)\s+\w+/i.test(line);  // Has matchup

    if (hasBettingContent || processedLines.length === 0) {
      processedLines.push(line);
    }
  }

  return processedLines.join('\n');
}

/**
 * Extract structured betting information
 */
function extractBettingInfo(text) {
  const info = {
    sport: null,
    teams: [],
    picks: [],
    capper: null,
    confidence: null,
    timestamp: null
  };

  // Extract sport
  for (const [sport, keywords] of Object.entries(SPORTS_MAP)) {
    if (keywords.some(kw => text.toLowerCase().includes(kw))) {
      info.sport = sport;
      break;
    }
  }

  // Extract capper
  for (const capper of KNOWN_CAPPERS) {
    if (text.toLowerCase().includes(capper.toLowerCase())) {
      info.capper = capper;
      break;
    }
  }

  // Extract teams (improved pattern)
  const teamPatterns = [
    /(\w+(?:\s+\w+)?)\s+(?:vs?\.?|@|versus)\s+(\w+(?:\s+\w+)?)/gi,
    /(\w+)\s*\/\s*(\w+)/g,
    /(\w+)\s+at\s+(\w+)/gi
  ];

  for (const pattern of teamPatterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      info.teams.push({
        away: match[1].trim(),
        home: match[2].trim()
      });
    }
  }

  // Extract individual picks with comprehensive parsing
  const lines = text.split('\n');
  for (const line of lines) {
    const pickInfo = extractPickFromLine(line);
    if (pickInfo) {
      info.picks.push(pickInfo);
    }
  }

  // Extract confidence level
  const confidenceMatch = text.match(/\b(MAX|max play|POD|POTD|lock|hammer|bomb|best bet|5\s*star)/i);
  if (confidenceMatch) {
    info.confidence = confidenceMatch[0].toUpperCase();
  }

  // Extract timestamp if present
  const timeMatch = text.match(/\d{1,2}:\d{2}\s*(am|pm)?/i);
  if (timeMatch) {
    info.timestamp = timeMatch[0];
  }

  return info;
}

/**
 * Extract pick details from a single line
 */
function extractPickFromLine(line) {
  if (!line || line.length < 5) return null;

  const pick = {
    raw: line,
    bet: null,
    odds: null,
    units: null,
    type: null
  };

  // Extract odds
  const oddsMatch = line.match(/([+-]\d{3,4})/);
  if (oddsMatch) {
    pick.odds = oddsMatch[1];
  }

  // Extract units
  const unitsMatch = line.match(/(\d+(?:\.\d+)?)\s*(?:units?|u)\b/i);
  if (unitsMatch) {
    pick.units = parseFloat(unitsMatch[1]);

    // Check for MAX play
    if (/\bmax\b/i.test(line)) {
      pick.units = `${pick.units}u MAX`;
    } else {
      pick.units = `${pick.units}u`;
    }
  }

  // Determine bet type
  for (const [type, pattern] of Object.entries(BET_PATTERNS)) {
    if (pattern.test(line)) {
      pick.type = type;
      break;
    }
  }

  // Clean the bet text
  pick.bet = line
    .replace(/([+-]\d{3,4})/g, '')        // Remove odds
    .replace(/\d+(?:\.\d+)?\s*u\b/gi, '') // Remove units
    .replace(/\bmax\b/gi, '')             // Remove MAX
    .replace(/^\d+\s*[\.\)]\s*/, '')      // Remove leading numbers
    .replace(/^[•\-\*]\s*/, '')           // Remove bullets
    .replace(/\s+/g, ' ')
    .trim();

  // Only return if we have meaningful content
  if (pick.bet && (pick.odds || pick.units || pick.type)) {
    return pick;
  }

  return null;
}

/**
 * Format picks for Discord output
 */
function formatForDiscord(bettingInfo, label = '') {
  let output = [];

  // Add label if provided
  if (label) {
    output.push(`**${label}**`);
  }

  // Add capper name
  if (bettingInfo.capper) {
    output.push(`**${bettingInfo.capper}**`);
  }

  // Add confidence level
  if (bettingInfo.confidence) {
    output.push(`🔥 **${bettingInfo.confidence}** 🔥`);
  }

  // Add sport
  if (bettingInfo.sport) {
    output.push(`*${bettingInfo.sport}*`);
  }

  // Format picks
  if (bettingInfo.picks.length > 0) {
    for (const pick of bettingInfo.picks) {
      let formatted = pick.bet;

      // Add bet type indicator
      if (pick.type === 'parlay') {
        formatted = `🎯 PARLAY: ${formatted}`;
      } else if (pick.type === 'prop') {
        formatted = `📊 PROP: ${formatted}`;
      }

      // Add odds
      if (pick.odds) {
        formatted += ` ${pick.odds}`;
      }

      // Add units
      if (pick.units) {
        formatted += ` (${pick.units})`;
      }

      output.push(formatted);
    }
  } else if (bettingInfo.teams.length > 0) {
    // If no formatted picks but we have teams, show them
    for (const team of bettingInfo.teams) {
      output.push(`${team.away} vs ${team.home}`);
    }
  }

  // Add timestamp if present
  if (bettingInfo.timestamp) {
    output.push(`_Posted at ${bettingInfo.timestamp}_`);
  }

  return output.join('\n');
}

/**
 * Main processing function
 */
function processOCRText(rawText, channelName = '') {
  // Deep clean the text
  const cleaned = deepCleanText(rawText);

  // Extract structured betting information
  const bettingInfo = extractBettingInfo(cleaned);

  // Format for Discord
  const formatted = formatForDiscord(bettingInfo, channelName);

  return {
    raw: rawText,
    cleaned: cleaned,
    formatted: formatted,
    bettingInfo: bettingInfo,
    hasContent: bettingInfo.picks.length > 0 || bettingInfo.teams.length > 0
  };
}

module.exports = {
  processOCRText,
  deepCleanText,
  extractBettingInfo,
  formatForDiscord,
  KNOWN_CAPPERS,
  SPORTS_MAP,
  BET_PATTERNS
};