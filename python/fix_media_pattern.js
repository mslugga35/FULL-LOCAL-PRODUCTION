const fs = require('fs');

// Read the current paid webhook sender
let content = fs.readFileSync('/root/bots/paid_webhook_sender.js', 'utf8');

// Fix the media finding pattern to match _media suffix
const oldPattern = /f\.startsWith\(base\) && \s*!f\.endsWith\('\.json'\)/g;
const newPattern = "(f.startsWith(base + '_media') || f.startsWith(base + '.')) && !f.endsWith('.json')";

// Replace the pattern
content = content.replace(
  'f.startsWith(base) &&',
  "(f.startsWith(base + '_media') || f.startsWith(base + '.')) &&"
);

// Also ensure we're looking for the right pattern
content = content.replace(
  /const base = jsonBasename\.replace\(\/\\.json$\/i?, ''\);/g,
  "const base = jsonBasename.replace(/\.json$/i, '');"
);

// Write back
fs.writeFileSync('/root/bots/paid_webhook_sender.js', content);
console.log('Fixed media pattern matching for _media suffix');
