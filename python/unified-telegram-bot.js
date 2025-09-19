/**
 * UNIFIED TELEGRAM BOT - ONE BOT FOR ALL CHANNELS
 * Monitors all required Telegram channels with a single session
 * Writes messages to inbox for Discord bots to consume
 */

require('dotenv').config();
const { TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const vision = require('@google-cloud/vision');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const CONFIG = {
  telegram: {
    apiId: parseInt(process.env.TELEGRAM_API_ID),
    apiHash: process.env.TELEGRAM_API_HASH,
    sessionString: process.env.TELEGRAM_SESSION
  },
  inbox: process.env.INBOX_DIR || 'C:\\Users\\mpmmo\\telegram_inbox',
  checkInterval: 30000 // 30 seconds
};

// All channels to monitor (consolidated from multiple bots)
const CHANNELS_TO_MONITOR = [
  // From paidcappers-bot
  { pattern: /uatb/i, folder: 'uatb', discord: 'paid' },
  { pattern: /diamond/i, folder: 'diamond', discord: 'paid' },
  { pattern: /chamba/i, folder: 'chamba', discord: 'paid' },
  
  // From discord-forwarder-ocr
  { pattern: /cappers\s*free/i, folder: 'cappers_free', discord: 'free' },
  { pattern: /cappers\s*leaked/i, folder: 'cappers_leaked', discord: 'leaked' },
  { pattern: /exclusive\s*cappers/i, folder: 'exclusive_cappers', discord: 'exclusive' }
];

// Initialize Google Vision if available
let visionClient = null;
try {
  const keyFile = path.join(__dirname, 'google-vision-key.json');
  if (require('fs').existsSync(keyFile)) {
    visionClient = new vision.ImageAnnotatorClient({ keyFilename: keyFile });
    console.log('✅ Google Vision initialized');
  }
} catch (error) {
  console.log('⚠️ Google Vision not available:', error.message);
}

class UnifiedTelegramBot {
  constructor() {
    this.client = null;
    this.channels = new Map();
    this.processedMessages = new Set();
    this.isRunning = false;
    this.stats = {
      startTime: Date.now(),
      messagesProcessed: 0,
      ocrProcessed: 0,
      errors: 0
    };
  }

  async initialize() {
    console.log('🚀 UNIFIED TELEGRAM BOT STARTING');
    console.log('=====================================');
    
    try {
      // Create inbox directories
      await this.ensureDirectories();
      
      // Load processed messages to avoid duplicates
      await this.loadProcessedMessages();
      
      // Connect to Telegram
      this.client = new TelegramClient(
        new StringSession(CONFIG.telegram.sessionString),
        CONFIG.telegram.apiId,
        CONFIG.telegram.apiHash,
        { connectionRetries: 5 }
      );
      
      await this.client.connect();
      const me = await this.client.getMe();
      console.log(`✅ Connected as: ${me.firstName || me.username || 'User'}`);
      
      // Find and map channels
      await this.findChannels();
      
      console.log('✅ Initialization complete!');
      console.log(`📊 Monitoring ${this.channels.size} channels`);
      console.log('=====================================\n');
      
      return true;
    } catch (error) {
      console.error('❌ Initialization failed:', error);
      return false;
    }
  }

  async ensureDirectories() {
    await fs.mkdir(CONFIG.inbox, { recursive: true });
    
    // Create subdirectories for each channel type
    for (const channel of CHANNELS_TO_MONITOR) {
      const dir = path.join(CONFIG.inbox, channel.folder);
      await fs.mkdir(dir, { recursive: true });
    }
    
    console.log(`✅ Created inbox directories at: ${CONFIG.inbox}`);
  }

  async loadProcessedMessages() {
    try {
      const stateFile = path.join(CONFIG.inbox, 'processed_today.json');
      const data = await fs.readFile(stateFile, 'utf8');
      const state = JSON.parse(data);
      
      // Check if it's still the same day
      const today = new Date().toDateString();
      if (state.date === today) {
        this.processedMessages = new Set(state.messages);
        console.log(`📋 Loaded ${this.processedMessages.size} processed messages from today`);
      } else {
        console.log('📅 New day - starting fresh');
      }
    } catch (error) {
      console.log('📋 No previous state - starting fresh');
    }
  }

  async saveProcessedMessages() {
    const stateFile = path.join(CONFIG.inbox, 'processed_today.json');
    const state = {
      date: new Date().toDateString(),
      messages: Array.from(this.processedMessages)
    };
    await fs.writeFile(stateFile, JSON.stringify(state, null, 2));
  }

  async findChannels() {
    console.log('\n🔍 Finding channels...');
    const dialogs = await this.client.getDialogs();
    
    for (const dialog of dialogs) {
      if (dialog.isChannel || dialog.isGroup) {
        const title = dialog.entity.title || '';
        
        // Check against all patterns
        for (const config of CHANNELS_TO_MONITOR) {
          if (config.pattern.test(title)) {
            this.channels.set(dialog.entity.id.toString(), {
              entity: dialog.entity,
              title: title,
              folder: config.folder,
              discord: config.discord
            });
            console.log(`  ✅ Found: "${title}" -> ${config.folder}/`);
            break;
          }
        }
      }
    }
    
    // Show which channels weren't found
    for (const config of CHANNELS_TO_MONITOR) {
      const found = Array.from(this.channels.values()).some(ch => ch.folder === config.folder);
      if (!found) {
        console.log(`  ⚠️ Not found: ${config.pattern.source}`);
      }
    }
  }

  async start() {
    this.isRunning = true;
    console.log('\n📡 Starting message monitoring...\n');
    
    // Initial fetch of today's messages
    await this.fetchTodaysMessages();
    
    // Then monitor for new messages
    while (this.isRunning) {
      try {
        await this.checkNewMessages();
        await new Promise(resolve => setTimeout(resolve, CONFIG.checkInterval));
      } catch (error) {
        console.error('❌ Monitor error:', error.message);
        this.stats.errors++;
        await new Promise(resolve => setTimeout(resolve, CONFIG.checkInterval));
      }
    }
  }

  async fetchTodaysMessages() {
    console.log('📥 Fetching today\'s messages...');
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayTimestamp = Math.floor(today.getTime() / 1000);
    
    for (const [channelId, channelInfo] of this.channels) {
      try {
        const messages = await this.client.getMessages(channelInfo.entity, {
          limit: 100,
          minDate: todayTimestamp
        });
        
        console.log(`  ${channelInfo.title}: ${messages.length} messages today`);
        
        for (const message of messages.reverse()) {
          await this.processMessage(message, channelInfo);
        }
      } catch (error) {
        console.error(`  ❌ Error fetching ${channelInfo.title}:`, error.message);
      }
    }
  }

  async checkNewMessages() {
    for (const [channelId, channelInfo] of this.channels) {
      try {
        const messages = await this.client.getMessages(channelInfo.entity, {
          limit: 10
        });
        
        for (const message of messages.reverse()) {
          await this.processMessage(message, channelInfo);
        }
      } catch (error) {
        // Silently continue - avoid spamming logs
      }
    }
  }

  async processMessage(message, channelInfo) {
    const messageId = `${channelInfo.title}_${message.id}`;
    
    // Skip if already processed
    if (this.processedMessages.has(messageId)) {
      return;
    }
    
    this.processedMessages.add(messageId);
    this.stats.messagesProcessed++;
    
    try {
      const messageData = {
        id: messageId,
        channel: channelInfo.title,
        folder: channelInfo.folder,
        discord: channelInfo.discord,
        messageId: message.id,
        date: message.date,
        timestamp: new Date(message.date * 1000).toISOString(),
        text: message.message || '',
        hasMedia: !!message.media
      };
      
      // Process media/screenshots with OCR
      if (message.media && message.media.photo) {
        try {
          const buffer = await this.client.downloadMedia(message.media);
          if (buffer && visionClient) {
            const ocrText = await this.performOCR(buffer);
            if (ocrText) {
              messageData.ocrText = ocrText;
              this.stats.ocrProcessed++;
              console.log(`  📸 OCR: ${channelInfo.title} - extracted text`);
            }
          }
          
          // Save the image
          const mediaFile = `${messageId}_media.jpg`;
          const mediaPath = path.join(CONFIG.inbox, channelInfo.folder, mediaFile);
          await fs.writeFile(mediaPath, buffer);
          messageData.mediaFile = mediaFile;
        } catch (error) {
          console.error(`  ❌ Media error:`, error.message);
        }
      }
      
      // Save message to inbox
      const filename = `${messageId}.json`;
      const filepath = path.join(CONFIG.inbox, channelInfo.folder, filename);
      await fs.writeFile(filepath, JSON.stringify(messageData, null, 2));
      
      const time = new Date(message.date * 1000).toLocaleTimeString();
      console.log(`📨 [${time}] ${channelInfo.title} -> ${channelInfo.folder}/${filename}`);
      
      // Save state periodically
      if (this.processedMessages.size % 10 === 0) {
        await this.saveProcessedMessages();
      }
      
    } catch (error) {
      console.error('❌ Process error:', error.message);
      this.stats.errors++;
    }
  }

  async performOCR(buffer) {
    try {
      const [result] = await visionClient.textDetection({
        image: { content: buffer.toString('base64') }
      });
      
      if (result.textAnnotations && result.textAnnotations.length > 0) {
        return result.textAnnotations[0].description.trim();
      }
      return null;
    } catch (error) {
      console.error('OCR error:', error.message);
      return null;
    }
  }

  async stop() {
    console.log('\n🛑 Stopping bot...');
    this.isRunning = false;
    
    // Save final state
    await this.saveProcessedMessages();
    
    // Show stats
    const runtime = Date.now() - this.stats.startTime;
    const hours = Math.floor(runtime / 3600000);
    const minutes = Math.floor((runtime % 3600000) / 60000);
    
    console.log('\n📊 Final Statistics:');
    console.log(`  Runtime: ${hours}h ${minutes}m`);
    console.log(`  Messages: ${this.stats.messagesProcessed}`);
    console.log(`  OCR Processed: ${this.stats.ocrProcessed}`);
    console.log(`  Errors: ${this.stats.errors}`);
    
    if (this.client) {
      await this.client.disconnect();
    }
  }
}

// Main execution
async function main() {
  const bot = new UnifiedTelegramBot();
  
  // Handle shutdown
  process.on('SIGINT', async () => {
    await bot.stop();
    process.exit(0);
  });
  
  process.on('SIGTERM', async () => {
    await bot.stop();
    process.exit(0);
  });
  
  // Initialize and start
  if (await bot.initialize()) {
    await bot.start();
  } else {
    console.error('❌ Failed to initialize bot');
    process.exit(1);
  }
}

// Start the bot
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = UnifiedTelegramBot;