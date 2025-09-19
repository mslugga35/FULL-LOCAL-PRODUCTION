#!/bin/bash
# Fix OCR processor - remove port binding issue

echo '=== Fixing OCR Processor ==='

# Backup current file
cp /root/bots/ocr-folder-processor.js /root/bots/ocr-folder-processor.js.bak

# Remove the problematic port binding lines
sed -i '/const PORT = /,/app.listen(PORT/d' /root/bots/ocr-folder-processor.js
sed -i '/📡 Status dashboard/d' /root/bots/ocr-folder-processor.js

# Also remove any Express app initialization if it exists without listeners
sed -i '/const express = require.*express/d' /root/bots/ocr-folder-processor.js
sed -i '/const app = express/d' /root/bots/ocr-folder-processor.js

echo 'OCR processor fixed - removed port binding'
