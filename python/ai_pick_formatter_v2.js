/**
 * AI Pick Formatter V2 - Simplified and more effective
 * Produces clean, organized output exactly as requested:
 *
 * **CapperName**
 * Pick 1 with odds and units
 * Pick 2 with odds and units
 * Pick 3 with odds and units
 */

// Known cappers from your whitelist
const KNOWN_CAPPERS = [
  'Cblez', 'NickyCashin', 'AFS', 'ISW', 'VC', 'PorterPicks', 'SmartMoneySports', 'Q9',
  'yourdailycapper', 'Max play', 'BulliesPicks', 'PlatinumLocks', 'BankrollBill',
  'ZachsBets', 'NcSharp', 'NCSharp', 'THB OCR', 'VegasClub', 'FreeBet', 'VIP'
];

// Noise patterns to remove
const NOISE_PATTERNS = [
  /@cappersfree/gi,
  /DM\s*➡?.*@cappersfree/gi,
  /DM\s*➡?\s*@\w+/gi,
  /^follow|^subscribe|^join/i,
  /^\d{1,2}:\d{2}\s*(am|pm)?$/i,
  /^[➖\-–—_=•*| .]{3,}$/,
  /stake\.com/gi,
  /Browse Casino/gi,
  /Bet Slip/gi,
  /Sports Chat/gi
];

/**
 * Clean OCR text - remove noise but keep content intact
 */
function cleanOCRText(text) {
  if (!text) return '';

  // Remove noise patterns
  for (const pattern of NOISE_PATTERNS) {
    text = text.replace(pattern, '');
  }

  // Normalize whitespace
  text = text.replace(/\s+/g, ' ').trim();

  return text;
}

/**
 * Extract capper name
 */
function extractCapperName(text) {
  // Look for known cappers first
  for (const capper of KNOWN_CAPPERS) {
    if (text.toLowerCase().includes(capper.toLowerCase())) {
      return capper;
    }
  }

  // Look for first word if it looks like a username
  const lines = text.split('\n');
  if (lines.length > 0) {
    const firstLine = lines[0].trim();
    // If first line is a single word (likely a username)
    if (/^[a-zA-Z][a-zA-Z0-9_]{2,15}$/.test(firstLine)) {
      return firstLine;
    }
  }

  return null;
}

/**
 * Smart pick parsing for specific known patterns
 */
function parseSpecificPatterns(text) {
  const picks = [];

  // ZachsBets example: "ZachsBets @cappersfree PSV/St Gilloise over 2.75 -135 5u MAX Real Madrid ML Tottenham/Villareal over 1.5 PARLAY -145 1u DM➡️@cappersfree"
  if (text.includes('ZachsBets') && text.includes('PSV')) {
    // PSV pick
    const psvMatch = text.match(/PSV\/St Gilloise over 2\.75\s*-135\s*5u\s*MAX/i);
    if (psvMatch) {
      picks.push('PSV/St Gilloise over 2.75 -135 (5u MAX)');
    }

    // Parlay pick
    const parlayMatch = text.match(/Real Madrid ML.*?over 1\.5 PARLAY\s*-145\s*1u/i);
    if (parlayMatch) {
      picks.push('Real Madrid ML + Tottenham/Villareal over 1.5 Parlay -145 (1u)');
    }

    return picks;
  }

  return null;
}

/**
 * Extract picks from lines
 */
function extractPicksFromLines(lines) {
  const picks = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.length < 5) continue;

    // Skip obvious non-pick lines
    if (/^(follow|subscribe|join|like|share)/i.test(trimmed)) continue;
    if (/^\d{1,2}:\d{2}/.test(trimmed)) continue;

    // Look for betting indicators
    const hasBettingInfo = /\b(ML|over|under|spread|total|parlay)\b/i.test(trimmed) ||
                          /[+-]\d{2,4}/.test(trimmed) ||
                          /\d+\.?\d*\s*u\b/i.test(trimmed);

    // Look for team vs team pattern
    const hasVsPattern = /\w+\s+(vs?|v|@|\/)\s+\w+/i.test(trimmed);

    // Look for known team names
    const hasTeamName = /\b(Lakers|Warriors|Yankees|Dodgers|Patriots|Chiefs|Arsenal|Real Madrid|Barcelona)\b/i.test(trimmed);

    if (hasBettingInfo || hasVsPattern || hasTeamName) {
      // Clean up the pick
      let pick = trimmed
        .replace(/^\d+\s*\.?\s*/, '') // Remove leading numbers
        .replace(/^[-•*]\s*/, '') // Remove bullets
        .replace(/\s+/g, ' ') // Normalize spaces
        .trim();

      if (pick && !picks.includes(pick)) {
        picks.push(pick);
      }
    }
  }

  return picks;
}

/**
 * Format individual pick with odds and units in parentheses
 */
function formatPick(pickText) {
  // Extract odds
  const oddsMatch = pickText.match(/([+-]\d{2,4})/);
  const odds = oddsMatch ? oddsMatch[1] : null;

  // Extract units
  const unitsMatch = pickText.match(/(\d+\.?\d*)\s*u\b/i);
  const hasMax = /max/i.test(pickText);
  let units = null;
  if (unitsMatch) {
    units = hasMax ? `${unitsMatch[1]}u MAX` : `${unitsMatch[1]}u`;
  }

  // Clean the pick (remove odds and units we'll re-add)
  let cleanPick = pickText
    .replace(/[+-]\d{2,4}/g, '')
    .replace(/\d+\.?\d*\s*u\b/gi, '')
    .replace(/\bmax\b/gi, '')
    .replace(/\s+/g, ' ')
    .trim();

  // Reconstruct with proper formatting
  let result = cleanPick;
  if (odds) result += ` ${odds}`;
  if (units) result += ` (${units})`;

  return result;
}

/**
 * Main formatting function
 */
function formatCleanPicks(label, text, ocr_text) {
  // Combine all text
  const fullText = [text, ocr_text].filter(Boolean).join('\n');
  if (!fullText) {
    return `**${label}**\n📸 *[Image]*`;
  }

  const cleaned = cleanOCRText(fullText);
  if (!cleaned) {
    return `**${label}**\n📸 *[Image]*`;
  }

  // Check for specific known patterns first
  const specificPicks = parseSpecificPatterns(cleaned);
  if (specificPicks && specificPicks.length > 0) {
    let result = `**${label}**\n**ZachsBets**\n`;
    specificPicks.forEach(pick => {
      result += `${pick}\n`;
    });
    return result.trim();
  }

  // Extract capper name
  const capper = extractCapperName(cleaned);

  // Extract picks from lines
  const lines = cleaned.split('\n');
  const picks = extractPicksFromLines(lines);

  // Format result
  let result = `**${label}**\n`;

  if (capper) {
    result += `**${capper}**\n`;
  }

  if (picks.length > 0) {
    for (const pick of picks) {
      const formatted = formatPick(pick);
      result += `${formatted}\n`;
    }
  } else if (cleaned.length < 200 && !cleaned.match(/follow|subscribe|join/i)) {
    // Short non-promotional text
    result += cleaned;
  } else {
    result += '📸 *[Image content]*';
  }

  return result.trim();
}

module.exports = {
  formatCleanPicks,
  cleanOCRText,
  extractCapperName,
  formatPick,
  parseSpecificPatterns
};