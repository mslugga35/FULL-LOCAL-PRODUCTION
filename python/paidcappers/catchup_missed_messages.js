/**
 * Catch up on messages from non-active hours (2AM - 8AM)
 * Can also be used to catch up on any missed time period
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

async function catchupMissedMessages(hoursBack = 24) {
  const discordClient = new Discord.Client({
    intents: [
      Discord.GatewayIntentBits.Guilds,
      Discord.GatewayIntentBits.GuildMessages,
      Discord.GatewayIntentBits.MessageContent,
    ],
  });

  const telegramClient = new TelegramClient(
    new StringSession(CONFIG.telegram.sessionString),
    CONFIG.telegram.apiId,
    CONFIG.telegram.apiHash,
    {
      connectionRetries: 5,
    }
  );

  try {
    console.log('[START] Initializing catch-up process...');
    
    await discordClient.login(CONFIG.discord.token);
    console.log('[OK] Discord connected');
    
    await telegramClient.start();
    console.log('[OK] Telegram connected');

    const discordChannel = await discordClient.channels.fetch(CONFIG.discord.channels.paidCappers);
    if (!discordChannel) {
      throw new Error('Discord channel not found');
    }

    // Calculate time range
    const startTime = new Date();
    startTime.setHours(startTime.getHours() - hoursBack);
    
    const endTime = new Date();
    
    console.log(`\n[CATCH-UP] Fetching messages from last ${hoursBack} hours`);
    console.log(`From: ${startTime.toLocaleString()}`);
    console.log(`To: ${endTime.toLocaleString()}\n`);
    
    const paidChannels = [
      { name: '🌐 UATB 🌐', id: 2177758646 },
      { name: 'DIAMOND 💎 VIP PACKAGE', id: 2470080886 }
    ];

    let totalSent = 0;
    
    for (const channelInfo of paidChannels) {
      console.log(`\n[CHECKING] ${channelInfo.name}...`);
      
      const dialogs = await telegramClient.getDialogs();
      const dialog = dialogs.find(d => d.entity.title === channelInfo.name);
      
      if (!dialog) {
        console.log(`  [SKIP] Channel not found`);
        continue;
      }

      // Get messages from time period
      const messages = await telegramClient.getMessages(dialog.entity, {
        limit: 500,
        offsetDate: Math.floor(endTime.getTime() / 1000)
      });

      const messagesInRange = [];
      
      for (const message of messages) {
        const messageDate = new Date(message.date * 1000);
        
        // Check if within our time range
        if (messageDate < startTime) break;
        if (messageDate > endTime) continue;
        
        // Check if message was during "sleep hours" (2 AM - 8 AM)
        const hour = messageDate.getHours();
        const wasDuringSleep = (hour >= 2 && hour < 8);
        
        messagesInRange.push({
          date: messageDate,
          text: message.text,
          hasMedia: !!message.media,
          wasDuringSleep,
          message
        });
      }
      
      console.log(`  [FOUND] ${messagesInRange.length} total messages`);
      
      // Sort chronologically (oldest first)
      messagesInRange.sort((a, b) => a.date - b.date);
      
      // Send each message to Discord
      for (const msgData of messagesInRange) {
        const sender = await msgData.message.getSender();
        const senderName = sender ? (sender.firstName || sender.username || 'Unknown') : 'Channel';
        
        let content = msgData.text || '';
        if (!content && msgData.hasMedia) {
          content = '[See attached media]';
        }
        
        if (!content && !msgData.hasMedia) continue;
        
        const sleepTag = msgData.wasDuringSleep ? ' [SLEEP HOURS]' : '';
        
        const discordMessage = `**PAID CAPPER PICK (CATCH-UP)${sleepTag}**
**From:** ${channelInfo.name} (${senderName})
**Time:** ${msgData.date.toLocaleString()}
**Message:**
${content}
========================================`;

        try {
          // Prepare message options
          const messageOptions = { content: discordMessage };
          
          // Download and attach media if available
          if (msgData.hasMedia && msgData.message.media) {
            try {
              if (msgData.message.media.photo || msgData.message.media.document) {
                console.log('    [MEDIA] Downloading...');
                const mediaBuffer = await telegramClient.downloadMedia(msgData.message, {});
                
                if (mediaBuffer) {
                  const extension = msgData.message.media.document ? 
                    (msgData.message.media.document.mimeType ? msgData.message.media.document.mimeType.split('/')[1] : 'jpg') : 
                    'jpg';
                  const filename = `catchup_${msgData.date.getTime()}.${extension}`;
                  const { AttachmentBuilder } = Discord;
                  const attachment = new AttachmentBuilder(mediaBuffer, { name: filename });
                  messageOptions.files = [attachment];
                  console.log(`    [MEDIA] Attached: ${filename}`);
                }
              }
            } catch (mediaErr) {
              console.error(`    [MEDIA ERROR] ${mediaErr.message}`);
            }
          }
          
          await discordChannel.send(messageOptions);
          totalSent++;
          console.log(`  [SENT] ${msgData.date.toLocaleTimeString()}${sleepTag}`);
          
          // Rate limit prevention
          await new Promise(resolve => setTimeout(resolve, 1000));
        } catch (err) {
          console.error(`  [ERROR] Failed to send: ${err.message}`);
        }
      }
    }
    
    console.log(`\n[COMPLETE] Sent ${totalSent} messages to Discord`);
    
    await discordClient.destroy();
    await telegramClient.disconnect();
    
  } catch (error) {
    console.error('[ERROR]', error);
  }
}

// Check command line arguments
const args = process.argv.slice(2);
const hoursBack = args[0] ? parseInt(args[0]) : 24;

console.log(`Running catch-up for last ${hoursBack} hours...\n`);
catchupMissedMessages(hoursBack).catch(console.error);
