#!/bin/bash

# Backup original
cp /root/bots/discord_sender.js /root/bots/discord_sender.js.backup

# Create the fixed version
cat > /root/bots/discord_sender_fixed.js << 'EOF'
const Discord = require('discord.js');
const fs = require('fs').promises;
const path = require('path');
require('dotenv').config();

class DiscordSender {
  constructor() {
    this.client = new Discord.Client({
      intents: [
        Discord.GatewayIntentBits.Guilds,
        Discord.GatewayIntentBits.GuildMessages,
        Discord.GatewayIntentBits.MessageContent,
        Discord.GatewayIntentBits.GuildMessageReactions
      ]
    });
    
    this.sentMessages = new Set();
    this.webhookClient = null;
    this.stats = {
      sent: 0,
      errors: 0,
      skipped: 0
    };
  }

  // Helper function to get title
  getTitle(message, folder) {
    return message.channel_title || 
           message.chat_title || 
           message.channelName ||
           message.from || 
           message.channel ||
           folder.replace(/_/g, ' ').toUpperCase() ||
           'Unknown';
  }

  // Helper function to get message ID
  getMessageId(message, filename) {
    return message.messageId || 
           message.id || 
           message.msg_id ||
           message.message_id ||
           filename.replace('.json', '') ||
           Date.now().toString();
  }

  // Helper function to get OCR text
  getOcrText(message) {
    return message.ocrText || 
           message.ocr_text || 
           message.ocr ||
           message.extracted_text ||
           '';
  }

  async start() {
    console.log('🚀 Starting Discord Sender...');
    
    // Setup Discord client
    this.client.once('ready', () => {
      console.log(`✅ Logged in as ${this.client.user.tag}`);
      console.log(`📊 Connected to ${this.client.guilds.cache.size} servers`);
      
      // List all guilds
      this.client.guilds.cache.forEach(guild => {
        console.log(`  - ${guild.name} (ID: ${guild.id})`);
      });
    });

    this.client.on('error', (error) => {
      console.error('Discord client error:', error);
    });

    // Login to Discord
    await this.client.login(process.env.DISCORD_BOT_TOKEN);
    
    // Start processing loop
    this.startProcessing();
  }

  async startProcessing() {
    console.log('🔄 Starting message processing loop...');
    
    // Process messages every 5 seconds
    setInterval(async () => {
      await this.processAllFolders();
    }, 5000);
  }

  async processAllFolders() {
    const folders = ['free_cappers', 'leaked_cappers', 'exclusive_cappers'];
    
    for (const folder of folders) {
      await this.processFolder(folder);
    }
  }

  async processFolder(folderName) {
    const folderPath = path.join('/root/bots/message_queue', folderName);
    
    try {
      const files = await fs.readdir(folderPath);
      const jsonFiles = files.filter(f => f.endsWith('.json'));
      
      for (const file of jsonFiles) {
        const filepath = path.join(folderPath, file);
        
        try {
          const data = await fs.readFile(filepath, 'utf8');
          const message = JSON.parse(data);
          
          // Skip if already sent
          const msgId = this.getMessageId(message, file);
          if (this.sentMessages.has(msgId)) {
            continue;
          }
          
          // Get safe values
          const title = this.getTitle(message, folderName);
          const ocrText = this.getOcrText(message);
          
          // Create Discord embed
          const embed = new Discord.EmbedBuilder()
            .setAuthor({ 
              name: `${folderName.includes('paid') ? '💎 PAID' : '🆓 FREE'} - ${title}`
            })
            .setTimestamp(new Date(message.timestamp || Date.now()))
            .setFooter({ text: `ID: ${msgId}` });
          
          // Set color based on folder
          if (folderName.includes('paid')) {
            embed.setColor('#FFD700'); // Gold for paid
          } else if (folderName.includes('sports')) {
            embed.setColor('#00FF00'); // Green for sports
          } else if (folderName.includes('leaked')) {
            embed.setColor('#FF4500'); // Orange for leaked
          } else if (folderName.includes('exclusive')) {
            embed.setColor('#9400D3'); // Purple for exclusive
          } else {
            embed.setColor('#0099FF'); // Blue for free
          }
          
          // Add message text
          if (message.text) {
            embed.setDescription(message.text);
          }
          
          // Add OCR text if available
          if (ocrText) {
            embed.addFields({ 
              name: '📸 OCR Text', 
              value: ocrText.substring(0, 1024) 
            });
          }
          
          // Send to appropriate channel
          await this.sendToChannel(embed, folderName);
          
          // Mark as sent
          this.sentMessages.add(msgId);
          this.stats.sent++;
          
          // Delete the processed file
          await fs.unlink(filepath);
          
          console.log(`✅ Sent message from ${folderName}: ${title}`);
          
        } catch (error) {
          console.error(`Error processing ${file}:`, error.message);
          this.stats.errors++;
        }
      }
    } catch (error) {
      if (error.code !== 'ENOENT') {
        console.error(`Error reading folder ${folderName}:`, error);
      }
    }
  }

  async sendToChannel(embed, folderName) {
    // Channel mappings
    const channelMappings = {
      'free_cappers': '1403894557615325216',      // #leaks
      'leaked_cappers': '1403894596186017962',    // #cappers-leaked
      'exclusive_cappers': '1403894653660692500'  // #exclusive-cappers
    };
    
    const channelId = channelMappings[folderName];
    if (!channelId) {
      console.error(`No channel mapping for ${folderName}`);
      return;
    }
    
    const channel = this.client.channels.cache.get(channelId);
    if (!channel) {
      console.error(`Channel ${channelId} not found for ${folderName}`);
      return;
    }
    
    await channel.send({ embeds: [embed] });
  }
}

// Start the bot
const bot = new DiscordSender();
bot.start().catch(console.error);

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down...');
  bot.client.destroy();
  process.exit(0);
});
EOF

# Replace the original with the fixed version
mv /root/bots/discord_sender_fixed.js /root/bots/discord_sender.js

echo 'Discord sender fixed and updated!'
SCRIPT_END'

chmod +x /root/bots/fix_discord_sender.sh && /root/bots/fix_discord_sender.sh
