const vision = require('@google-cloud/vision');
const fs = require('fs').promises;
const path = require('path');
const formatter = require('./ai_pick_formatter');
const axios = require('axios');

// Google Vision client
const visionClient = new vision.ImageAnnotatorClient({
  keyFilename: '/root/bots/credentials/google-vision-key.json'
});

// Webhook URLs - use the paid webhook for testing
const WEBHOOK_URL = 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN';

async function sendToDiscord(text, channelName) {
  try {
    const payload = {
      username: 'THB OCR (Clean)',
      avatar_url: 'https://i.imgur.com/4M34hi2.png',
      embeds: [{
        title: '📢 ' + channelName.replace(/_/g, ' ').toUpperCase(),
        description: text,
        color: 0x00FF00,
        footer: {
          text: 'Processed with Google Vision OCR (90%+ accuracy)'
        },
        timestamp: new Date().toISOString()
      }]
    };
    
    const response = await axios.post(WEBHOOK_URL, payload);
    console.log('✅ Sent clean message to Discord');
    return true;
  } catch (error) {
    console.error('Discord webhook error:', error.message);
    return false;
  }
}

async function processAndSend() {
  const inboxDir = '/root/inbox';
  const files = await fs.readdir(inboxDir);
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  
  const todayImages = files.filter(f => 
    f.startsWith(today) && (f.endsWith('.jpg') || f.endsWith('.png'))
  );
  
  console.log(`Found ${todayImages.length} images from today`);
  console.log('Processing first 5 as test...');
  
  // Process first 5 images as test
  for (const image of todayImages.slice(0, 5)) {
    const imagePath = path.join(inboxDir, image);
    console.log('\nProcessing:', image);
    
    try {
      const imageBuffer = await fs.readFile(imagePath);
      const [result] = await visionClient.textDetection({
        image: { content: imageBuffer.toString('base64') }
      });
      
      if (result.textAnnotations && result.textAnnotations.length > 0) {
        const rawText = result.textAnnotations[0].description;
        const processed = formatter.processOCRText(rawText, 'free_cappers');
        
        console.log('Clean text preview:');
        console.log(processed.formatted.substring(0, 100) + '...');
        
        // Send to Discord
        await sendToDiscord(processed.formatted, 'free_cappers');
        
        // Wait between messages
        await new Promise(resolve => setTimeout(resolve, 3000));
      } else {
        console.log('No text found in image');
      }
    } catch (error) {
      console.error('Error processing:', error.message);
    }
  }
  
  console.log('\n✅ Test complete - check Discord for clean messages');
}

processAndSend().catch(console.error);
