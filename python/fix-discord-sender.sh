#!/bin/bash
# Fix Discord sender to handle missing fields gracefully

echo '=== Fixing Discord Sender ==='

# Backup current file
cp /root/bots/discord_sender.js /root/bots/discord_sender.js.bak

# Create a patch to fix the undefined issues
cat > /tmp/sender-fix.js << 'JSFIX'
// Find the section where we build the message content
// This patch makes the sender bulletproof against missing fields

// Helper to get channel name from folder
function getChannelLabel(folder) {
  const labels = {
    'free_cappers': 'FREE',
    'leaked_cappers': 'LEAKED', 
    'exclusive_cappers': 'EXCLUSIVE',
    'paid_uatb': 'UATB',
    'paid_diamond': 'DIAMOND',
    'paid_cappers': 'PAID'
  };
  return labels[folder] || folder.replace(/_/g, ' ').toUpperCase();
}

// Helper to build message content
function buildMessageContent(message, folder, filename) {
  // Get title with fallbacks
  const fallbackTitle = folder.replace(/_/g, ' ');
  const title = (
    message.chat_title || 
    message.channel_title || 
    message.channelName ||
    message.from ||
    fallbackTitle
  ).toString().trim() || fallbackTitle;
  
  // Get message ID with fallbacks
  const msgId = String(
    message.message_id || 
    message.messageId || 
    message.id ||
    filename.replace('.json', '')
  );
  
  // Get OCR text (check both possible field names)
  const ocrText = message.ocr_text || message.ocrText || message.ocr || '';
  
  // Build message parts
  const parts = [];
  const label = getChannelLabel(folder);
  
  // Add header
  parts.push();
  
  // Add message ID
  parts.push();
  
  // Add date if available
  if (message.date || message.timestamp) {
    parts.push();
  }
  
  // Add main text if available
  if (message.text && message.text.trim()) {
    parts.push('');
  }
  
  // Add OCR text if available
  if (ocrText && ocrText.trim()) {
    parts.push('');
    parts.push('📸 **OCR Text:**');
    parts.push('');
  }
  
  // Join and ensure we don't exceed Discord limit
  let content = parts.join('\n');
  if (content.length > 2000) {
    content = content.substring(0, 1997) + '...';
  }
  
  return content;
}
JSFIX

echo 'Discord sender fix created'
