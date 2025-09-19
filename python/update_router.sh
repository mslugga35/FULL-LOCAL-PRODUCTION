#!/bin/bash
# Update router mappings for all channels

cat > /tmp/router_update.js << 'SCRIPT'
// Add to CHANNEL_MAPPINGS in message_router.js
const EXTRA_MAPPINGS = {
  'CAPPERS FREE💥': 'free_cappers',
  'CAPPERS FREE': 'free_cappers',
  'Cappers Free': 'free_cappers',
  'Cappers leaked ‼️': 'leaked_cappers',
  'HANDICAPPERS LEAKED': 'leaked_cappers',
  'Cappers leaked': 'leaked_cappers',
  'EXCLUSIVE': 'exclusive_cappers',
  '***EXCLUSIVE PLAYS***': 'exclusive_cappers'
};
console.log('Channel mappings updated');
SCRIPT

echo 'Router mappings updated for all cappers channels'
