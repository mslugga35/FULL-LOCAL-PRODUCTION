/**
 * Message Enhancer - Based on discord-forwarder-bot parser logic
 * Cleans and formats OCR text using proven patterns
 */

// Known cappers from your whitelist
const KNOWN_CAPPERS = [
  'Cblez', 'NickyCashin', 'AFS', 'ISW', 'VC', 'PorterPicks', 'SmartMoneySports', 'Q9',
  'yourdailycapper', 'Max play', 'BulliesPicks', 'PlatinumLocks', 'BankrollBill',
  'ZachsBets', 'NcSharp', 'NCSharp', 'THB OCR'
];

// Noise patterns to remove
const NOISE_PATTERNS = [
  /@cappersfree/gi,
  /DM\s*➡?.*@cappersfree/gi,
  /^follow|^subscribe/i,
  /^\d{1,2}:\d{2}\s*(am|pm)?$/i,
  /^[➖\-–—_=•*| .]{3,}$/,
  /stake\.com/gi,
  /Browse Casino/gi,
  /Bet Slip/gi,
  /Sports Chat/gi
];

// Team names for pick detection
const TEAMS = [
  'tigers', 'yankees', 'mets', 'royals', 'rangers', 'marlins', 'phillies',
  'angels', 'astros', 'dodgers', 'giants', 'cubs', 'brewers', 'cardinals',
  'reds', 'pirates', 'braves', 'nationals', 'guardians', 'white sox', 'blue jays',
  'rays', 'orioles', 'red sox', 'mariners', 'athletics', 'twins', 'indians',
  'padres', 'rockies', 'diamondbacks', 'miami', 'boston', 'cleveland',
  'texans', 'buccaneers', 'arsenal', 'tottenham', 'villareal', 'real madrid'
];

function cleanOCRText(text) {
  if (!text) return '';

  // Remove common OCR artifacts
  text = text.replace(/\s+/g, ' ');
  text = text.replace(/([a-z])([A-Z])/g, '$1 $2'); // Split camelCase

  // Remove noise patterns
  for (const pattern of NOISE_PATTERNS) {
    text = text.replace(pattern, '');
  }

  return text.trim();
}

function extractCapperName(text) {
  // Method 1: Look for known cappers - check more carefully
  for (const capper of KNOWN_CAPPERS) {
    // Use word boundary for exact matches
    const regex = new RegExp(`\\b${capper}\\b`, 'i');
    if (regex.test(text)) {
      return capper;
    }
  }

  // Method 2: Look for @username pattern
  const atMatch = text.match(/@(\w+)/);
  if (atMatch && atMatch[1] !== 'cappersfree') {
    return atMatch[1];
  }

  // Method 3: Look for "Capper:" pattern
  const capperMatch = text.match(/(?:Capper|From|By):\s*([A-Za-z0-9_]+)/i);
  if (capperMatch) {
    return capperMatch[1];
  }

  // Method 4: Look at start of text for username-like pattern
  // Common pattern: "username KBO" or "username MLB"
  const startMatch = text.match(/^([a-zA-Z][a-zA-Z0-9_]{2,})\s+(?:KBO|MLB|NFL|NBA|NHL|NCAAB|NCAAF)/i);
  if (startMatch) {
    return startMatch[1];
  }

  // Method 5: CamelCase names like BankrollBill
  const camelMatch = text.match(/\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b/);
  if (camelMatch) {
    return camelMatch[1];
  }

  // Method 6: First word if it looks like a username (not a common word)
  const firstWord = text.split(/[\s\n]/)[0];
  if (firstWord &&
      firstWord.length > 2 &&
      firstWord.length < 20 &&
      /^[a-zA-Z]/.test(firstWord) &&
      !/^(MLB|NBA|NFL|NHL|KBO|NCAAB|NCAAF|over|under|total|spread)/i.test(firstWord)) {
    return firstWord;
  }

  return null;
}

function extractPicks(text) {
  const picks = [];
  const lines = text.split(/[\n.]/);

  for (const line of lines) {
    const cleanLine = line.trim();
    if (cleanLine.length < 3) continue;

    // Check for betting patterns
    const hasBettingInfo =
      /\b(ML|moneyline|over|under|spread|total)\b/i.test(cleanLine) ||
      /[+-]\d+\.?\d*/.test(cleanLine) ||
      /\d+\.?\d*\s*(unit|units|u)\b/i.test(cleanLine) ||
      /\b(f5|1h|2h|1st\s*half|first\s*half)\b/i.test(cleanLine);

    // Check for team names
    const hasTeam = TEAMS.some(team =>
      new RegExp(`\\b${team}\\b`, 'i').test(cleanLine)
    );

    // If line has both team and betting info, or clear betting pattern
    if ((hasTeam && hasBettingInfo) || hasBettingInfo) {
      // Clean up the pick
      let pick = cleanLine
        .replace(/^\d+\s*\.?\s*/, '') // Remove leading numbers
        .replace(/^[-•]\s*/, '') // Remove bullets
        .trim();

      if (pick && !picks.includes(pick)) {
        picks.push(pick);
      }
    }
  }

  return picks;
}

function formatEnhancedMessage(label, text, ocr_text) {
  // Start with label
  let formatted = `**${label}**\n`;

  // If we have actual text content, check if it's a capper name
  if (text && text.trim()) {
    // Check if text looks like a capper identifier
    const textLines = text.split('\n');
    const firstLine = textLines[0].trim();

    // If first line looks like a capper name (no spaces, alphanumeric)
    if (firstLine && /^[a-zA-Z0-9_]+$/.test(firstLine)) {
      formatted += `📍 **From: ${firstLine}**\n`;
      formatted += '━━━━━━━━━\n';
    } else if (text.trim()) {
      // Otherwise just add the text
      formatted += text + '\n';
    }
  }

  // Process OCR text for picks
  if (ocr_text) {
    const cleaned = cleanOCRText(ocr_text);
    const capper = extractCapperName(cleaned);
    const picks = extractPicks(cleaned);

    // If we found a capper in OCR and didn't already add one from text
    if (capper && !formatted.includes('**From:')) {
      formatted += `📍 **From: ${capper}**\n`;
      formatted += '━━━━━━━━━\n';
    }

    if (picks.length > 0) {
      formatted += '**Picks:**\n';
      for (const pick of picks) {
        formatted += `• ${pick}\n`;
      }
    } else if (cleaned) {
      // If no picks extracted, just show cleaned text
      formatted += cleaned;
    }
  }

  return formatted;
}

module.exports = {
  cleanOCRText,
  extractCapperName,
  extractPicks,
  formatEnhancedMessage
};