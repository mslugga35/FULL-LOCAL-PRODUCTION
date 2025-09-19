const vision = require('@google-cloud/vision');
const fs = require('fs').promises;
const path = require('path');
const formatter = require('./ai_pick_formatter');

const client = new vision.ImageAnnotatorClient({
  keyFilename: '/root/bots/credentials/google-vision-key.json'
});

async function processImage(imagePath, channelName = 'free_cappers') {
  try {
    console.log('Processing:', path.basename(imagePath));
    
    const imageBuffer = await fs.readFile(imagePath);
    const [result] = await client.textDetection({
      image: { content: imageBuffer.toString('base64') }
    });
    
    if (result.textAnnotations && result.textAnnotations.length > 0) {
      const rawText = result.textAnnotations[0].description;
      const processed = formatter.processOCRText(rawText, channelName);
      
      // Create clean message JSON
      const message = {
        timestamp: new Date().toISOString(),
        channelName: channelName,
        source: 'google_vision',
        ocr_processor: 'google_vision',
        ocr_text: processed.formatted,
        has_media: true,
        mediaPath: imagePath,
        capperName: processed.capperName || 'Unknown',
        bettingInfo: processed.bettingInfo,
        sent_to_discord: false
      };
      
      // Save to queue with clean filename
      const baseName = path.basename(imagePath, path.extname(imagePath));
      const jsonPath = `/root/bots/message_queue/${channelName}/${baseName}.json`;
      await fs.writeFile(jsonPath, JSON.stringify(message, null, 2));
      
      console.log('Created:', jsonPath);
      console.log('Clean text:', processed.formatted.substring(0, 100) + '...');
      return jsonPath;
    } else {
      console.log('No text found in image');
      return null;
    }
  } catch (error) {
    console.error('Error processing:', error.message);
    return null;
  }
}

async function processAll() {
  const inboxDir = '/root/inbox';
  const files = await fs.readdir(inboxDir);
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  
  const todayImages = files.filter(f => 
    f.startsWith(today) && (f.endsWith('.jpg') || f.endsWith('.png'))
  );
  
  console.log(`Found ${todayImages.length} images from today`);
  
  for (const image of todayImages) {
    const imagePath = path.join(inboxDir, image);
    await processImage(imagePath);
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

if (require.main === module) {
  processAll().catch(console.error);
}

module.exports = { processImage };
