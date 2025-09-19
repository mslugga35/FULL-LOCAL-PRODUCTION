#!/bin/bash
echo "========================================"
echo "TESTING TODAY'S MESSAGES - ALL BOTS"
echo "========================================"
echo

TODAY=$(date +%Y%m%d)
echo "Testing messages from: $TODAY"
echo

# Function to process messages for a specific folder
process_folder() {
    local folder=$1
    local channel_name=$2
    
    echo "[PROCESSING] $folder ($channel_name)"
    
    # Create test folder
    mkdir -p /root/bots/message_queue/$folder
    
    # Count messages
    count=$(ls /root/inbox/*$TODAY* 2>/dev/null | wc -l)
    echo "Found $count messages for today"
    
    # Copy relevant messages based on folder type
    cd /root/inbox
    case $folder in
        "paid_uatb")
            cp *$TODAY*uatb* /root/bots/message_queue/$folder/ 2>/dev/null
            cp *$TODAY*UATB* /root/bots/message_queue/$folder/ 2>/dev/null
            ;;
        "paid_diamond")
            cp *$TODAY*diamond* /root/bots/message_queue/$folder/ 2>/dev/null
            cp *$TODAY*Diamond* /root/bots/message_queue/$folder/ 2>/dev/null
            ;;
        "leaked_cappers")
            cp *$TODAY*leaked* /root/bots/message_queue/$folder/ 2>/dev/null
            cp *$TODAY*8502* /root/bots/message_queue/$folder/ 2>/dev/null
            ;;
        "exclusive_cappers")
            cp *$TODAY*exclusive* /root/bots/message_queue/$folder/ 2>/dev/null
            ;;
        *)
            # Default to free_cappers for others
            cp *$TODAY* /root/bots/message_queue/$folder/ 2>/dev/null
            ;;
    esac
    
    # Process images in the folder
    cd /root/bots/message_queue/$folder
    for img in *.jpg 2>/dev/null; do
        if [ -f "$img" ]; then
            base=${img%.jpg}
            
            # Rename to _media.jpg format
            mv "$img" "${base}_media.jpg"
            
            # Create JSON file
            cat > "${base}.json" << JSONEOF
{
  "id": "${base##*_}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "channelId": "test_$folder",
  "channelName": "$channel_name",
  "has_media": true,
  "media_path": "${base}_media.jpg",
  "text": "Test message from $TODAY",
  "requires_ocr": true
}
JSONEOF
            echo "Created: ${base}.json"
        fi
    done
    
    processed=$(ls *.json 2>/dev/null | wc -l)
    echo "Processed $processed files for $folder"
    echo
}

# Process all bot folders
echo "[1/5] Processing Free Cappers..."
process_folder "free_cappers" "Free Cappers"

echo "[2/5] Processing Leaked Cappers..."  
process_folder "leaked_cappers" "Leaked Cappers"

echo "[3/5] Processing Exclusive Cappers..."
process_folder "exclusive_cappers" "Exclusive Cappers"

echo "[4/5] Processing Paid UATB..."
process_folder "paid_uatb" "Paid UATB"

echo "[5/5] Processing Paid Diamond..."
process_folder "paid_diamond" "Paid Diamond"

echo "========================================"
echo "RUNNING GOOGLE VISION OCR ON ALL"
echo "========================================"

# Run OCR processing
timeout 60 node -e "
const vision = require('@google-cloud/vision');
const fs = require('fs');
const path = require('path');
const formatter = require('./ai_pick_formatter');

const client = new vision.ImageAnnotatorClient({
  keyFilename: '/root/bots/credentials/google-vision-key.json'
});

const folders = ['free_cappers', 'leaked_cappers', 'exclusive_cappers', 'paid_uatb', 'paid_diamond'];

async function processAllFolders() {
  for (const folder of folders) {
    console.log('Processing folder:', folder);
    const folderPath = '/root/bots/message_queue/' + folder;
    
    try {
      const files = fs.readdirSync(folderPath).filter(f => f.endsWith('_media.jpg'));
      console.log('Found', files.length, 'images in', folder);
      
      for (const imgFile of files) {
        try {
          const imgPath = path.join(folderPath, imgFile);
          const jsonFile = imgFile.replace('_media.jpg', '.json');
          const jsonPath = path.join(folderPath, jsonFile);
          
          const imageBuffer = fs.readFileSync(imgPath);
          const [result] = await client.textDetection({
            image: { content: imageBuffer.toString('base64') }
          });
          
          if (result.textAnnotations && result.textAnnotations.length > 0) {
            const rawText = result.textAnnotations[0].description;
            const processed = formatter.processOCRText(rawText, folder);
            
            const message = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
            message.ocr_text = processed.formatted;
            message.ocr_raw = rawText;
            message.ocr_processor = 'google_vision';
            message.betting_info = processed.bettingInfo;
            message.formatter_version = 'google_vision_v1';
            
            fs.writeFileSync(jsonPath, JSON.stringify(message, null, 2));
            console.log('✅ Processed:', folder + '/' + jsonFile);
          }
        } catch (error) {
          console.error('❌ Error processing', imgFile, ':', error.message);
        }
      }
    } catch (error) {
      console.error('Error accessing folder', folder, ':', error.message);
    }
  }
  
  console.log('\n========================================');
  console.log('OCR PROCESSING COMPLETE');
  console.log('========================================');
}

processAllFolders().catch(console.error);
"

echo
echo "========================================"
echo "TESTING COMPLETE - CHECK DISCORD"
echo "========================================"
echo
echo "RESULTS SUMMARY:"
for folder in free_cappers leaked_cappers exclusive_cappers paid_uatb paid_diamond; do
    count=$(ls /root/bots/message_queue/$folder/*.json 2>/dev/null | wc -l)
    echo "- $folder: $count messages processed"
done

echo
echo "MONITORING COMMANDS:"
echo "- Watch OCR: pm2 logs google-vision-ocr"
echo "- Watch Discord: pm2 logs discord-sender"
echo "- Check queues: ls -la /root/bots/message_queue/*/"
echo
