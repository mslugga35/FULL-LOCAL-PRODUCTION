require('dotenv').config();
/**
 * IMPROVED OCR VERSION - Better text parsing and formatting
 * Fixes messy OCR output with smart parsing
 */

const { TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const Discord = require('discord.js');
const vision = require('@google-cloud/vision');
const express = require('express');
const fs = require('fs');
const path = require('path');

// Express for keep-alive
const app = express();
const PORT = process.env.OCR_PORT || 3005; // Changed to unique port 3005 for OCR bot

// Initialize Google Vision
let visionClient;
try {
  visionClient = new vision.ImageAnnotatorClient({
    keyFilename: 'google-vision-key.json'
  });
  console.log('✅ Google Vision initialized');
} catch (error) {
  console.log('⚠️  Google Vision not configured:', error.message);
}

const CONFIG = {
  discord: {
    token: process.env.DISCORD_OCR_BOT_TOKEN,
    channels: {
      cappersFreeLikes: "1403894557615325216",  // #leaks
      cappersLeaked: "1403894596186017962",     // #cappers-leaked  
      exclusiveCappers: "1403894653660692500"   // #exclusive-cappers
    }
  },
  telegram: {
    apiId: parseInt(process.env.TELEGRAM_API_ID),
    apiHash: process.env.TELEGRAM_API_HASH,
    sessionString: process.env.TELEGRAM_SESSION
  }
};

// Channel mapping
const ALLOWED_CHANNELS = {
  'CAPPERS FREE💥': {
    discord: 'cappersFreeLikes',
    requiresOCR: true
  },
  'Cappers leaked ‼️': {
    discord: 'cappersLeaked',
    requiresOCR: true
  },
  '👑 Exclusive Cappers 👑': {
    discord: 'exclusiveCappers',
    requiresOCR: true
  }
};

class ImprovedOCRBot {
  constructor() {
    this.stats = {
      startTime: new Date(),
      messagesProcessed: 0,
      ocrSuccess: 0,
      errors: 0
    };
    this.processedMessages = new Set();
    this.isRunning = false;
  }

  async initialize() {
    console.log('🚀 IMPROVED OCR BOT');
    console.log('=====================================');
    console.log(`Google Vision: ${visionClient ? 'ENABLED ✅' : 'DISABLED ❌'}`);
    
    // Connect Discord
    this.discord = new Discord.Client({
      intents: [
        Discord.GatewayIntentBits.Guilds,
        Discord.GatewayIntentBits.GuildMessages,
        Discord.GatewayIntentBits.MessageContent
      ]
    });
    
    await this.discord.login(CONFIG.discord.token);
    console.log(`✅ Discord: ${this.discord.user.tag}`);
    
    // Verify Discord channels
    for (const [name, id] of Object.entries(CONFIG.discord.channels)) {
      try {
        const channel = await this.discord.channels.fetch(id);
        console.log(`  ✅ ${name}: #${channel.name}`);
      } catch (error) {
        console.log(`  ❌ ${name}: Channel ${id} not found!`);
      }
    }
    
    // Connect Telegram
    const session = new StringSession(CONFIG.telegram.sessionString);
    this.telegram = new TelegramClient(
      session,
      CONFIG.telegram.apiId,
      CONFIG.telegram.apiHash,
      { connectionRetries: 5 }
    );
    
    await this.telegram.connect();
    const me = await this.telegram.getMe();
    console.log(`✅ Telegram: ${me.firstName || me.username}`);
    
    // Find channels
    await this.findChannels();
    
    console.log('\n✅ Ready! Starting monitoring...');
    return true;
  }

  async findChannels() {
    console.log('\n🔍 Finding channels...');
    const dialogs = await this.telegram.getDialogs();
    this.channels = [];
    
    for (const dialog of dialogs) {
      const title = dialog.title || '';
      
      if (ALLOWED_CHANNELS[title]) {
        const config = ALLOWED_CHANNELS[title];
        
        this.channels.push({
          title: title,
          entity: dialog.entity,
          discordChannel: config.discord
        });
        
        console.log(`✅ Found: ${title} → ${config.discord}`);
      }
    }
    
    console.log(`📊 Monitoring ${this.channels.length} channels`);
  }

  async start() {
    this.isRunning = true;
    console.log('\n📡 Started monitoring...\n');
    
    while (this.isRunning) {
      try {
        await this.checkMessages();
        await new Promise(r => setTimeout(r, 30000)); // 30 seconds
      } catch (error) {
        console.error('❌ Error:', error.message);
        this.stats.errors++;
        await new Promise(r => setTimeout(r, 30000));
      }
    }
  }

  async checkMessages() {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayTimestamp = Math.floor(today.getTime() / 1000);
    
    for (const channel of this.channels) {
      try {
        const messages = await this.telegram.getMessages(channel.entity, {
          limit: 10,
          minDate: todayTimestamp
        });
        
        for (const msg of messages) {
          const msgId = `${channel.title}_${msg.id}`;
          
          if (this.processedMessages.has(msgId)) continue;
          this.processedMessages.add(msgId);
          
          await this.processMessage(msg, channel);
        }
        
      } catch (error) {
        console.error(`❌ Error in ${channel.title}: ${error.message}`);
      }
    }
  }

  async processMessage(msg, channel) {
    this.stats.messagesProcessed++;
    const time = new Date(msg.date * 1000).toLocaleTimeString();
    console.log(`📨 [${time}] ${channel.title}`);
    
    // Get Discord channel
    const discordChannelId = CONFIG.discord.channels[channel.discordChannel];
    const discordChannel = await this.discord.channels.fetch(discordChannelId);
    
    if (msg.media && msg.photo) {
      // Screenshot - do OCR
      try {
        const buffer = await this.telegram.downloadMedia(msg.media, {});
        let ocrText = '';
        let capperName = msg.message || '';
        
        if (visionClient && buffer) {
          // Use Google Vision
          const [result] = await visionClient.textDetection({
            image: { content: buffer.toString('base64') }
          });
          
          if (result.textAnnotations?.length > 0) {
            ocrText = result.textAnnotations[0].description;
            this.stats.ocrSuccess++;
            console.log('   ✅ OCR successful');
            
            // Parse and format the OCR text properly
            const parsed = this.parseOCRText(ocrText, capperName);
            
            if (parsed.picks.length > 0 || parsed.content) {
              // Send formatted message
              await discordChannel.send(parsed.formatted);
              console.log('   ✅ Forwarded with clean formatting');
            } else {
              // No valid picks found
              console.log('   ⚠️  No valid picks detected');
              await discordChannel.send(`**${this.cleanCapperName(capperName)}**\n_[No clear picks detected in image]_`);
            }
            
          } else {
            console.log('   ⚠️  No text in image');
            await discordChannel.send(`**${this.cleanCapperName(capperName)}**\n_[Image with no readable text]_`);
          }
        } else {
          // No OCR available
          console.log('   ⚠️  No OCR available');
          await discordChannel.send(`**${this.cleanCapperName(capperName)}**\n_[OCR not available]_`);
        }
        
      } catch (error) {
        console.error(`   ❌ Processing error: ${error.message}`);
        this.stats.errors++;
      }
      
    } else if (msg.message) {
      // Text message - forward as is
      try {
        const cleanText = this.cleanCapperName(msg.message);
        if (cleanText && cleanText.length > 5) {
          await discordChannel.send(`**${cleanText}**`);
          console.log('   ✅ Text forwarded');
        }
      } catch (error) {
        console.error(`   ❌ Text error: ${error.message}`);
      }
    }
  }

  parseOCRText(ocrText, capperName) {
    // Clean the capper name
    const cleanCapper = this.cleanCapperName(capperName);
    
    // Clean up OCR artifacts and noise
    let cleaned = ocrText
      .replace(/\bili\b/gi, '') // Remove random "lli" artifacts
      .replace(/\b00\b/g, '')   // Remove standalone "00"
      .replace(/➖+/g, '')       // Remove dividers
      .replace(/@cappersfree/gi, '')
      .replace(/HANDICAPPERS\s*LEAKED/gi, '')
      .replace(/CAPPERS\s*PICKS/gi, '')
      .replace(/DM➡️.*$/gm, '')
      .replace(/Join.*$/gmi, '')
      .replace(/Subscribe.*$/gmi, '')
      .replace(/Follow.*$/gmi, '')
      .replace(/Payout.*$/gmi, '')
      .replace(/Stake.*$/gmi, '')
      .replace(/Odds.*$/gmi, '')
      .trim();
    
    // Fix common OCR mistakes
    cleaned = cleaned
      .replace(/022\.0/g, 'O22.0')
      .replace(/023\.0/g, 'O23.0')
      .replace(/021\.5/g, 'O21.5')
      .replace(/04\.5/g, 'O4.5')
      .replace(/\s+ML\s+/g, ' ML ')
      .replace(/\s+([+-]\d+)/g, ' $1');
    
    // Split into lines and filter
    const lines = cleaned.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 3);
    
    const picks = [];
    const parlays = [];
    let currentCapper = cleanCapper;
    
    for (const line of lines) {
      // Check if this is a capper name
      if (this.isCapperName(line)) {
        currentCapper = line;
        continue;
      }
      
      // Check if this is a valid pick
      if (this.isValidPick(line)) {
        // Clean up the pick format
        const cleanPick = this.cleanPickFormat(line);
        
        if (line.toLowerCase().includes('parlay')) {
          parlays.push(cleanPick);
        } else {
          picks.push(cleanPick);
        }
      }
    }
    
    // Format the final message
    let formatted = `**${currentCapper}**\n`;
    
    if (picks.length > 0) {
      formatted += picks.map(p => `• ${p}`).join('\n');
    }
    
    if (parlays.length > 0) {
      if (picks.length > 0) formatted += '\n\n';
      formatted += '**Parlays:**\n';
      formatted += parlays.map(p => `• ${p}`).join('\n');
    }
    
    // If no picks found, return the cleaned text
    if (picks.length === 0 && parlays.length === 0) {
      formatted = `**${currentCapper}**\n\`\`\`\n${cleaned.substring(0, 1500)}\n\`\`\``;
    }
    
    return {
      picks,
      parlays,
      formatted: formatted.trim(),
      content: cleaned
    };
  }

  isCapperName(text) {
    // Known cappers
    const knownCappers = [
      'Vinny', 'AlgoPicks', 'KingCap', 'HammeringHank', 'VegasNinja',
      'Mojo', 'SetPointBets', 'NickyCashin', 'Codycoversspreads',
      'Sauce & Toast', 'SolananSierra'
    ];
    
    return knownCappers.some(capper => 
      text.toLowerCase().includes(capper.toLowerCase())
    );
  }

  isValidPick(text) {
    // Must have betting indicators
    const patterns = [
      /\bML\b/i,                    // Moneyline
      /[+-]\d{1,4}(\.\d)?/,        // Spreads/Odds
      /\b[OU]\d+\.?\d*/i,          // Over/Under
      /\bover\s+\d+/i,             // Over
      /\bunder\s+\d+/i,            // Under
      /\d+(\.\d+)?\s*units?/i,     // Units
      /\bBTTS\b/i,                 // Both teams to score
      /\bPOTD\b/i,                 // Pick of the day
      /F5/,                        // First 5 innings
      /\d+u\b/i                    // Units shorthand
    ];
    
    // Must also have team/player names or sports
    const hasTeamOrSport = /[A-Z][a-z]+\s+[A-Z]|MLB|NBA|NFL|NHL|UFC|WNBA|Tennis|Soccer/;
    
    return patterns.some(p => p.test(text)) && 
           (hasTeamOrSport.test(text) || text.split(' ').length > 2);
  }

  cleanPickFormat(text) {
    // Clean up formatting
    return text
      .replace(/\s+/g, ' ')           // Normalize spaces
      .replace(/([A-Za-z])(\d)/g, '$1 $2')  // Add space between letters and numbers
      .replace(/(\d)([A-Za-z])/g, '$1 $2')  // Add space between numbers and letters
      .replace(/\s+([+-])/g, ' $1')   // Ensure space before +/-
      .replace(/\bU\s+(\d)/gi, 'U$1') // Fix units format
      .replace(/\s*-\s*/g, ' ')       // Clean up dashes
      .trim();
  }

  cleanCapperName(text) {
    if (!text) return 'Picks';
    
    // Extract first meaningful line as capper name
    const firstLine = text.split('\n')[0]
      .replace(/[🔥💰💥✅🎯💎🏆⚡️]/g, '')
      .replace(/➖+/g, '')
      .replace(/^@/, '')
      .trim();
    
    // If it's too long or contains picks, just return "Picks"
    if (firstLine.length > 30 || /\b(ML|units?|[+-]\d+)\b/i.test(firstLine)) {
      return 'Picks';
    }
    
    return firstLine || 'Picks';
  }

  getStats() {
    const uptime = Math.floor((Date.now() - this.stats.startTime) / 1000);
    return {
      uptime: `${Math.floor(uptime/3600)}h ${Math.floor((uptime%3600)/60)}m`,
      processed: this.stats.messagesProcessed,
      ocrSuccess: this.stats.ocrSuccess,
      errors: this.stats.errors,
      ocrRate: this.stats.messagesProcessed > 0 
        ? Math.round(this.stats.ocrSuccess / this.stats.messagesProcessed * 100) 
        : 0
    };
  }
}

// Web dashboard
app.get('/', (req, res) => {
  const stats = bot ? bot.getStats() : {};
  
  res.send(`
    <html>
      <head>
        <title>Improved OCR Bot</title>
        <meta http-equiv="refresh" content="30">
        <style>
          body { font-family: Arial; padding: 20px; background: #667eea; color: white; }
          .card { background: white; color: #333; padding: 20px; border-radius: 10px; }
        </style>
      </head>
      <body>
        <h1>📸 Improved OCR Bot</h1>
        <div class="card">
          <h2>Status: ${bot ? 'RUNNING' : 'STARTING'}</h2>
          <p>Google Vision: ${visionClient ? '✅ Enabled' : '❌ Disabled'}</p>
          <p>Uptime: ${stats.uptime || '0h 0m'}</p>
          <p>Messages: ${stats.processed || 0}</p>
          <p>OCR Success: ${stats.ocrSuccess || 0} (${stats.ocrRate || 0}%)</p>
          <p>Errors: ${stats.errors || 0}</p>
        </div>
      </body>
    </html>
  `);
});

app.get('/health', (req, res) => {
  const stats = bot ? bot.getStats() : {};
  res.json({
    status: bot ? 'healthy' : 'starting',
    googleVision: visionClient ? 'enabled' : 'disabled',
    ...stats
  });
});

app.listen(PORT, () => {
  console.log(`📡 Dashboard at http://localhost:${PORT}`);
});

// Start bot
let bot = null;

async function main() {
  bot = new ImprovedOCRBot();
  
  if (await bot.initialize()) {
    await bot.start();
  } else {
    console.error('❌ Failed to initialize');
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Shutting down...');
  if (bot) bot.isRunning = false;
  process.exit(0);
});

// Start
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});