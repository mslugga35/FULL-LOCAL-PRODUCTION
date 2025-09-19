#!/bin/bash
# Fix message router to move images along with JSON files

cat > /tmp/router_fix.js << 'JSEOF'
  async routeMessage(filePath) {
    try {
      // Read the message
      const data = await fs.readFile(filePath, 'utf8');
      const message = JSON.parse(data);
      
      // Determine destination folder
      const folder = this.determineFolder(message);
      
      if (!folder) {
        console.log(`  ⚠️  Cannot route ${path.basename(filePath)} - unknown channel`);
        return;
      }

      // Move to appropriate queue folder
      const destDir = path.join(QUEUE_DIR, folder);
      const destPath = path.join(destDir, path.basename(filePath));
      
      // Add routing info to message
      message.routed_from = 'inbox';
      message.routed_to = folder;
      message.routed_at = new Date().toISOString();
      
      // Write to destination
      await fs.writeFile(destPath, JSON.stringify(message, null, 2));
      
      // Move media file if it exists
      if (message.media_file) {
        const mediaSourcePath = path.join(INBOX_DIR, message.media_file);
        const mediaDestPath = path.join(destDir, message.media_file);
        
        try {
          await fs.access(mediaSourcePath);
          await fs.rename(mediaSourcePath, mediaDestPath);
          console.log(`    📸 Moved image: ${message.media_file}`);
        } catch (err) {
          console.log(`    ⚠️  Image not found: ${message.media_file}`);
        }
      }
      
      // Delete from inbox
      await fs.unlink(filePath);
      
      console.log(`  ✅ Routed to ${folder}: ${path.basename(filePath)}`);
      this.stats.routed++;
      
    } catch (error) {
      console.error(`  ❌ Error routing ${path.basename(filePath)}:`, error.message);
      this.stats.errors++;
    }
    
    this.stats.processed++;
  }
JSEOF

# Update the routeMessage function in message_router.js
sed -i '/async routeMessage/,/^  \}/c\' /root/bots/message_router.js
cat /tmp/router_fix.js >> /root/bots/message_router.js

echo 'Message router updated to move images!'
