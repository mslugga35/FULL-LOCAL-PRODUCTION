/**
 * Fetch all of today's UATB messages directly from Telegram
 * Includes all media (images, videos) and text
 */

require('dotenv').config({ path: __dirname + '/.env' });
const { Api, TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const fs = require('fs').promises;
const path = require('path');
const FormData = require('form-data');
const axios = require('axios');

// Configuration
const SESSION_FILE = 'telegram_session.txt';
const apiId = parseInt(process.env.TELEGRAM_API_ID) || 29479443;
const apiHash = process.env.TELEGRAM_API_HASH || 'e3a7a7226cf446bbfd5366f7da75cdfa';

// UATB Channel
const UATB_CHANNEL_ID = -1002379669995;
const UATB_CHANNEL_NAME = '🌐 UATB/PROPS 🌐';

// Discord Webhook for UATB
const WEBHOOK_URL = 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN';

// Output directory
const OUTPUT_DIR = '/root/bots/uatb_today';

async function sendToDiscordWebhook(text, mediaBuffer = null, mediaType = null) {
  try {
    const formData = new FormData();

    // Add message content
    const payload = {
      content: text || '📸 UATB Media',
      username: '🌐 UATB Bot'
    };

    formData.append('payload_json', JSON.stringify(payload));

    // Add media if present
    if (mediaBuffer) {
      const extension = mediaType === 'video' ? 'mp4' : 'jpg';
      const filename = `uatb_${Date.now()}.${extension}`;
      formData.append('files[0]', mediaBuffer, {
        filename: filename,
        contentType: mediaType === 'video' ? 'video/mp4' : 'image/jpeg'
      });
    }

    // Send to webhook
    const response = await axios.post(WEBHOOK_URL, formData, {
      headers: formData.getHeaders(),
      maxContentLength: Infinity,
      maxBodyLength: Infinity
    });

    console.log('✅ Sent to Discord');
    return true;
  } catch (error) {
    console.error('❌ Discord webhook error:', error.message);
    return false;
  }
}

async function fetchTodayMessages() {
  console.log('🚀 Starting UATB message fetch...');

  try {
    // Create output directory
    await fs.mkdir(OUTPUT_DIR, { recursive: true });

    // Initialize Telegram client
    const sessionString = await fs.readFile(SESSION_FILE, 'utf-8');
    const session = new StringSession(sessionString);

    const client = new TelegramClient(session, apiId, apiHash, {
      connectionRetries: 5,
    });

    await client.connect();
    console.log('✅ Connected to Telegram');

    // Get UATB channel
    const channel = await client.getEntity(UATB_CHANNEL_ID);
    console.log(`📥 Fetching from: ${UATB_CHANNEL_NAME}`);

    // Get today's date
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayTimestamp = Math.floor(today.getTime() / 1000);

    // Fetch messages from today (max 100)
    const messages = await client.getMessages(channel, {
      limit: 100
    });

    console.log(`📊 Found ${messages.length} recent messages`);

    let processedCount = 0;
    let todayCount = 0;

    for (const message of messages) {
      // Check if message is from today
      if (message.date < todayTimestamp) {
        console.log('⏸️  Reached yesterday messages, stopping');
        break;
      }

      todayCount++;

      const time = new Date(message.date * 1000).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      });

      let messageText = `**[${time}]**\n`;
      let hasMedia = false;
      let mediaBuffer = null;
      let mediaType = null;

      // Add message text
      if (message.message) {
        messageText += message.message;
      }

      // Handle media
      if (message.media) {
        if (message.media.photo) {
          hasMedia = true;
          mediaType = 'image';
          console.log(`  📸 Downloading image from message ${message.id}...`);
          mediaBuffer = await client.downloadMedia(message.media);
        } else if (message.media.video || message.media.document) {
          hasMedia = true;
          mediaType = 'video';
          console.log(`  🎥 Downloading video from message ${message.id}...`);
          mediaBuffer = await client.downloadMedia(message.media);
        }
      }

      // Send to Discord
      if (messageText || hasMedia) {
        console.log(`  📤 Sending to Discord: ${hasMedia ? 'with media' : 'text only'}`);
        await sendToDiscordWebhook(messageText, mediaBuffer, mediaType);
        processedCount++;

        // Save locally for backup
        const filename = `uatb_${message.id}_${message.date}.json`;
        await fs.writeFile(
          path.join(OUTPUT_DIR, filename),
          JSON.stringify({
            id: message.id,
            date: message.date,
            time: time,
            text: message.message || '',
            has_media: hasMedia,
            media_type: mediaType
          }, null, 2)
        );

        if (mediaBuffer && hasMedia) {
          const mediaFile = `uatb_${message.id}_${message.date}.${mediaType === 'video' ? 'mp4' : 'jpg'}`;
          await fs.writeFile(path.join(OUTPUT_DIR, mediaFile), mediaBuffer);
        }

        // Rate limit
        await new Promise(resolve => setTimeout(resolve, 1500));
      }
    }

    // Disconnect
    await client.disconnect();

    console.log('\n' + '='.repeat(50));
    console.log(`✅ COMPLETE: Processed ${processedCount} messages from today`);
    console.log(`📊 Total today's messages: ${todayCount}`);
    console.log(`💾 Saved to: ${OUTPUT_DIR}`);
    console.log('='.repeat(50));

  } catch (error) {
    console.error('❌ Error:', error);
  }
}

// Run
fetchTodayMessages().catch(console.error);
