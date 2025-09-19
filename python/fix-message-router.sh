#!/bin/bash
# Fix message router to move images with JSON

echo '=== Updating Message Router ==='

# Find the routeMessage function and add image handling
cat >> /tmp/router-patch.txt << 'PATCH'
      // Move media file if it exists
      if (message.media_file || message.mediaFile) {
        const mediaFileName = message.media_file || message.mediaFile;
        const mediaSourcePath = path.join(INBOX_DIR, mediaFileName);
        const mediaDestPath = path.join(destDir, mediaFileName);
        
        try {
          await fs.access(mediaSourcePath);
          await fs.rename(mediaSourcePath, mediaDestPath);
          console.log(`    📸 Moved image: ${mediaFileName}`);
        } catch (err) {
          // Also try with common extensions if exact file not found
          const baseName = path.basename(mediaFileName, path.extname(mediaFileName));
          const extensions = ['.jpg', '.jpeg', '.png', '.webp'];
          for (const ext of extensions) {
            try {
              const altSource = path.join(INBOX_DIR, baseName + ext);
              const altDest = path.join(destDir, baseName + ext);
              await fs.access(altSource);
              await fs.rename(altSource, altDest);
              console.log(`    📸 Moved image: ${baseName}${ext}`);
              break;
            } catch {}
          }
        }
      }
PATCH

# Check if image moving code already exists
if ! grep -q 'Moved image' /root/bots/message_router.js; then
  # Find the line after message routing and add our patch
  sed -i '/console.log.*Routed to/r /tmp/router-patch.txt' /root/bots/message_router.js
  echo 'Message router updated with image handling'
else
  echo 'Message router already has image handling'
fi

rm -f /tmp/router-patch.txt
