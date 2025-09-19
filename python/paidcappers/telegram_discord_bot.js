/**
 * Paid Cappers Telegram to Discord Bot
 * Forwards messages from Telegram to Discord
 */

require('dotenv').config();
const { TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const Discord = require('discord.js');

const CONFIG = {
  discord: {
    token: process.env.DISCORD_OCR_BOT_TOKEN,
    channels: {
      paidCappers: process.env.UATB_CHANNEL || "1403837637730762875"
    }
  },
  telegram: {
    apiId: parseInt(process.env.TELEGRAM_API_ID),
    apiHash: process.env.TELEGRAM_API_HASH,
    sessionString: process.env.TELEGRAM_SESSION
  }
};

class PaidCappersBot {
  constructor() {
    this.discordClient = new Discord.Client({
      intents: [
        Discord.GatewayIntentBits.Guilds,
        Discord.GatewayIntentBits.GuildMessages,
        Discord.GatewayIntentBits.MessageContent,
      ],
    });

    this.telegramClient = new TelegramClient(
      new StringSession(CONFIG.telegram.sessionString),
      CONFIG.telegram.apiId,
      CONFIG.telegram.apiHash,
      {
        connectionRetries: 5,
      }
    );

    this.isReady = false;
  }

  async initialize() {
    try {
      console.log('[START] Initializing Paid Cappers Bot...');

      // Connect to Discord
      await this.discordClient.login(CONFIG.discord.token);
      console.log('[OK] Discord client connected');

      // Connect to Telegram
      await this.telegramClient.start();
      console.log('[OK] Telegram client connected');

      this.isReady = true;
      this.setupEventHandlers();
      
      console.log('[READY] Bot is ready to forward messages!');
      
    } catch (error) {
      console.error('[ERROR] Failed to initialize:', error);
      process.exit(1);
    }
  }

  setupEventHandlers() {
    // Discord ready event
    this.discordClient.once('ready', () => {
      console.log(`[DISCORD] Logged in as ${this.discordClient.user.tag}`);
    });

    // Telegram new message handler - using NewMessage event
    const { NewMessage } = require('telegram/events');
    
    this.telegramClient.addEventHandler(async (event) => {
      await this.handleTelegramMessage(event.message);
    }, new NewMessage({}));
  }

  async handleTelegramMessage(message) {
    try {
      if (!this.isReady) return;

      // Time filter: Only capture messages between 8:00 AM - 2:00 AM
      const now = new Date();
      const currentHour = now.getHours();
      
      // Active hours: 8 AM (8) to 2 AM (2) next day
      // This means: 8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,0,1,2
      const isActiveHours = currentHour >= 8 || currentHour <= 2;
      
      if (!isActiveHours) {
        console.log(`[SLEEP] Bot sleeping - current time: ${now.toLocaleTimeString()} (active 8AM-2AM)`);
        return;
      }

      // Get message info
      const chat = await message.getChat();
      const sender = await message.getSender();
      
      let chatTitle = chat.title || 'Unknown Channel';
      
      // Custom display names for specific channels
      if (chatTitle.includes('DIAMOND') || chatTitle.includes('VIP PACKAGE')) {
        chatTitle = 'Chamba';
      }
      
      const senderName = sender ? (sender.firstName || sender.username || 'Unknown') : 'Unknown';
      const messageText = message.text || '[Media/File - No text content]';
      
      // Filter: Only forward messages from specific paid channels (using exact IDs)
      const allowedChannelIds = [
        -1002177758646, // 🌐 UATB 🌐
        -1002470080886, // DIAMOND 💎 VIP PACKAGE
        2177758646,     // 🌐 UATB 🌐 (positive ID format)
        2470080886      // DIAMOND 💎 VIP PACKAGE (positive ID format)
      ];
      
      // Convert BigInt to Number for comparison
      const chatId = Number(chat.id);
      const isAllowedChannel = allowedChannelIds.includes(chatId) || 
                              allowedChannelIds.includes(-100 + Math.abs(chatId));
      
      if (!isAllowedChannel) {
        console.log(`[SKIP] Ignoring message from: ${chatTitle} (ID: ${chatId}) - not a paid capper channel`);
        return;
      }
      
      const timestamp = new Date().toLocaleString();
      console.log(`[FORWARD] Processing message from ${chatTitle} (ID: ${chatId}) at ${timestamp}`);

      // Check if message has media (photo/document)
      let mediaBuffer = null;
      let mediaFilename = null;
      
      if (message.media) {
        try {
          if (message.media.photo || message.media.document) {
            console.log('[MEDIA] Downloading media attachment...');
            mediaBuffer = await this.telegramClient.downloadMedia(message, {});
            
            if (mediaBuffer) {
              const dateStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
              const extension = message.media.document ? 
                (message.media.document.mimeType ? message.media.document.mimeType.split('/')[1] : 'jpg') : 
                'jpg';
              mediaFilename = `${chatTitle.replace(/[^a-z0-9]/gi, '_')}_${dateStr}.${extension}`;
              console.log(`[MEDIA] Downloaded: ${mediaFilename}`);
            }
          }
        } catch (err) {
          console.error('[ERROR] Failed to download media:', err);
        }
      }

      // Format Discord message
      const discordMessage = `**From:** ${chatTitle} (${senderName})
**Time:** ${timestamp}
**Message:**
${messageText}
========================================`;

      // Send to Discord with media if available
      await this.sendToDiscord(discordMessage, mediaBuffer, mediaFilename);

    } catch (error) {
      console.error('[ERROR] Error handling Telegram message:', error);
    }
  }

  async sendToDiscord(message, mediaBuffer = null, mediaFilename = null) {
    try {
      const channelId = CONFIG.discord.channels.paidCappers;
      const channel = await this.discordClient.channels.fetch(channelId);
      
      if (!channel) {
        console.error('[ERROR] Discord channel not found:', channelId);
        return;
      }

      // Prepare message options
      const messageOptions = { content: message };
      
      // Add media attachment if available
      if (mediaBuffer && mediaFilename) {
        const attachment = new Discord.AttachmentBuilder(mediaBuffer, { name: mediaFilename });
        messageOptions.files = [attachment];
        console.log(`[OK] Sending message with media: ${mediaFilename}`);
      }

      await channel.send(messageOptions);
      console.log('[OK] Message sent to Discord');

    } catch (error) {
      console.error('[ERROR] Failed to send to Discord:', error);
    }
  }

  async start() {
    await this.initialize();
    
    // Keep the bot running
    process.on('SIGINT', async () => {
      console.log('\n[STOP] Shutting down bot...');
      await this.discordClient.destroy();
      await this.telegramClient.disconnect();
      process.exit(0);
    });

    console.log('[INFO] Bot is running. Press Ctrl+C to stop.');
  }
}

// Start the bot
const bot = new PaidCappersBot();
bot.start().catch(console.error);