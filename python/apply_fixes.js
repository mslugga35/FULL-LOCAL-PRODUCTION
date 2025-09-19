const fs = require('fs').promises;

async function applyFixes() {
  console.log('Applying critical fixes to discord_sender.js...');
  
  // Read the current file
  let content = await fs.readFile('discord_sender.js', 'utf-8');
  
  // 1. Add message enhancer import
  if (!content.includes('formatEnhancedMessage')) {
    content = content.replace(
      "const path = require('path');",
      "const path = require('path');\nconst { formatEnhancedMessage } = require('./message_enhancer');"
    );
  }
  
  // 2. Add isPaid flag to folder mapping
  content = content.replace(
    /(\s+)'free_cappers': \{ channel: 'free_cappers', label: '📢 Free' \}/,
    "$1'free_cappers': { channel: 'free_cappers', label: '📢 Free', isPaid: false }"
  );
  
  content = content.replace(
    /(\s+)'leaked_cappers': \{ channel: 'leaked_cappers', label: '🔓 Leaked' \}/,
    "$1'leaked_cappers': { channel: 'leaked_cappers', label: '🔓 Leaked', isPaid: false }"
  );
  
  content = content.replace(
    /(\s+)'exclusive_cappers': \{ channel: 'exclusive_cappers', label: '⭐ Exclusive' \}/,
    "$1'exclusive_cappers': { channel: 'exclusive_cappers', label: '⭐ Exclusive', isPaid: false }"
  );
  
  content = content.replace(
    /(\s+)'paid_uatb': \{ channel: 'uatb_diamond', label: '🌐 UATB 🌐' \}/,
    "$1'paid_uatb': { channel: 'uatb_diamond', label: '🌐 UATB 🌐', isPaid: true }"
  );
  
  content = content.replace(
    /(\s+)'paid_diamond': \{ channel: 'uatb_diamond', label: '💎 Chamba 💎' \}/,
    "$1'paid_diamond': { channel: 'uatb_diamond', label: '💎 Chamba 💎', isPaid: true }"
  );
  
  content = content.replace(
    /(\s+)'paid_chamba': \{ channel: 'uatb_diamond', label: '💎 Chamba 💎' \}/,
    "$1'paid_chamba': { channel: 'uatb_diamond', label: '💎 Chamba 💎', isPaid: true }"
  );
  
  content = content.replace(
    /(\s+)'paid_cappers': \{ channel: 'paid_cappers', label: '💰 Paid' \}/,
    "$1'paid_cappers': { channel: 'paid_cappers', label: '💰 Paid', isPaid: true }"
  );
  
  // 3. Fix the sendToDiscord method to use folder-based logic
  content = content.replace(
    /const isPaidChannel = channelId === "1403837637730762875";/,
    'const mapping = FOLDER_MAPPING[folderName];\n      const isPaidFolder = mapping && mapping.isPaid;'
  );
  
  content = content.replace(
    /if \(isPaidChannel && imagePath\)/,
    'if (isPaidFolder && imagePath)'
  );
  
  // 4. Update sendToDiscord signature to include folderName
  content = content.replace(
    /async sendToDiscord\(channelId, content, imagePath = null\)/,
    'async sendToDiscord(channelId, content, imagePath = null, folderName = null)'
  );
  
  // 5. Fix the processMessage method to use message enhancer for free channels
  const processMessageFix = `      if (isPaidFolder) {
        // PAID CHANNELS: Send EXACTLY as-is from Telegram INCLUDING IMAGES
        message = \;

        // Use whatever text is available, prioritizing caption for images
        if (msg.caption && msg.caption.trim()) {
          message += msg.caption;
        } else if (msg.text && msg.text.trim()) {
          message += msg.text;
        } else if (msg.ocr_text && msg.ocr_text.trim()) {
          message += msg.ocr_text;
        } else if (msg.has_media) {
          message += '📸 *[Image]*';
        } else {
          console.log(\);
          return;
        }
      } else {
        // FREE/LEAKED: Use enhanced formatting with OCR
        if (msg.ocr_text || msg.text || msg.caption) {
          message = formatEnhancedMessage(
            mapping.label,
            msg.text || msg.caption,
            msg.ocr_text
          );
        } else if (msg.has_media) {
          message = \;
        } else {
          console.log(\);
          return;
        }

        if (!message || message.trim() === \) {
          console.log(\);
          return;
        }
      }`;
  
  // Replace the existing message formatting logic
  content = content.replace(
    /if \(isPaidFolder\) \{[\s\S]*?\} else \{[\s\S]*?\}/,
    processMessageFix
  );
  
  // 6. Update the sendToDiscord call to pass folderName
  content = content.replace(
    /const success = await this\.sendToDiscord\(channelId, message, imagePath\);/,
    'const success = await this.sendToDiscord(channelId, message, imagePath, folderName);'
  );
  
  // 7. Fix image handling to copy first for paid channels
  const imageHandlingFix = `        // CRITICAL FIX: Handle image files properly for paid vs free
        if (msg.media_file) {
          try {
            const srcImg = path.join(CONFIG.queueDir, folderName, msg.media_file);
            const dstImg = path.join(processedPath, msg.media_file);
            
            if (mapping.isPaid) {
              // For paid channels, copy first then clean up after delay
              await fs.copyFile(srcImg, dstImg);
              console.log(\);
              
              // Clean up original after Discord has time to upload
              setTimeout(async () => {
                try {
                  await fs.unlink(srcImg);
                  console.log(\);
                } catch (err) {
                  // File might already be gone
                }
              }, 10000);
            } else {
              // For free channels, just move it
              await fs.rename(srcImg, dstImg);
            }
          } catch (err) {
            console.log(\);
          }
        }`;
  
  content = content.replace(
    /\/\/ Move image if exists[\s\S]*?catch \{[\s\S]*?\}/,
    imageHandlingFix
  );
  
  // Write the fixed file
  await fs.writeFile('discord_sender_fixed.js', content);
  console.log('Fixed file created: discord_sender_fixed.js');
}

applyFixes().catch(console.error);
