/**
 * OCR worker: scans queue folders, processes images, writes OCR text back into JSON.
 * Handles media_file field and resolves paths intelligently
 */

process.on('uncaughtException', e => { console.error('[FATAL]', e); process.exitCode = 1; });
process.on('unhandledRejection', e => { console.error('[FATAL]', e); process.exitCode = 1; });

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const { execFile } = require('child_process');
const { promisify } = require('util');
const execFileAsync = promisify(execFile);

// Core paths
const QUEUE_ROOT = '/root/bots/message_queue';
const INBOX_DIR = '/root/inbox';  // where images actually are
const TMP_DIR = '/root/bots/tmp';

// Folders to scan
const FOLDERS_TO_CHECK = [
  'free_cappers','leaked_cappers','exclusive_cappers','paid_cappers','paid_diamond','paid_uatb'
];
const SCAN_INTERVAL_MS = Number(process.env.OCR_SCAN_MS || 2000);

// Ensure tmp exists
fs.mkdirSync(TMP_DIR, { recursive: true });

// Optional Google Vision
let visionClient = null;
try {
  if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    const vision = require('@google-cloud/vision');
    visionClient = new vision.ImageAnnotatorClient();
    console.log('[INFO] Google Vision API initialized');
  }
} catch (e) {
  console.error('[WARN] Vision not available:', e?.message);
}

// Smart image path resolver
function resolveImagePath(jsonPath, rec) {
  const dirOfJson = path.dirname(jsonPath);
  const tryPaths = [];

  // 1) explicit fields with full/relative paths
  ['media_path','localImagePath','local_image_path','image_path','filepath'].forEach(k => {
    if (rec[k]) tryPaths.push(rec[k]);
  });

  // 2) filename only (media_file) - this is what we usually have
  if (rec.media_file) {
    tryPaths.push(path.join(dirOfJson, rec.media_file));    // same folder as JSON
    tryPaths.push(path.join(INBOX_DIR, rec.media_file));    // /root/inbox (WHERE THEY ACTUALLY ARE)
    tryPaths.push(path.join(QUEUE_ROOT, rec.media_file));   // queue root (rare)
    tryPaths.push(path.join('/root/bots/inbox', rec.media_file)); // alternative inbox location
  }

  for (const p of tryPaths) {
    try {
      if (fs.existsSync(p)) {
        console.log(`[FOUND] Image: ${p}`);
        return path.resolve(p);
      }
    } catch {}
  }

  console.log(`[NOT FOUND] Tried paths:`, tryPaths);
  return null;
}

// Google Vision OCR
async function ocrVision(img) {
  if (!visionClient) throw new Error('no_vision');
  const [res] = await visionClient.textDetection(img);
  const detections = res?.textAnnotations;
  if (detections && detections.length > 0) {
    return detections[0].description.trim();
  }
  return '';
}

// Tesseract OCR fallback
async function ocrTesseract(img) {
  try {
    const { stdout } = await execFileAsync('tesseract',[img,'stdout','-l','eng','--psm','6']);
    return (stdout || '').trim();
  } catch (e) {
    console.error('[TESSERACT error]', e.message);
    return '';
  }
}

// Clean up OCR text
function cleanupText(t) {
  if (!t) return '';
  return t.replace(/\s+/g,' ').trim();
}

// Main OCR pipeline
async function ocrPipeline(imgPath) {
  console.log(`[OCR] Processing: ${path.basename(imgPath)}`);

  let text = '';

  // Try Google Vision first
  if (visionClient) {
    try {
      text = await ocrVision(imgPath);
      console.log(`[GCV] Extracted ${text.length} chars`);
    } catch (e) {
      console.log('[GCV] Failed:', e.message);
    }
  }

  // Fallback to Tesseract
  if (!text || text.length < 5) {
    text = await ocrTesseract(imgPath);
    console.log(`[TESSERACT] Extracted ${text.length} chars`);
  }

  return cleanupText(text);
}

// Process single JSON file
async function processJsonFile(jsonPath) {
  const raw = await fsp.readFile(jsonPath, 'utf8');
  const rec = JSON.parse(raw);

  if (!rec.needs_ocr) {
    console.log('[SKIP needs_ocr=false]', path.basename(jsonPath));
    return { skip: true };
  }

  if (!rec.has_media) {
    console.log('[SKIP has_media=false]', path.basename(jsonPath));
    return { skip: true };
  }

  const img = resolveImagePath(jsonPath, rec);
  if (!img) {
    console.log('[SKIP no_image_found]', path.basename(jsonPath));
    return { skip: true };
  }

  const text = await ocrPipeline(img);

  // Update record
  rec.ocr_text = text || '';
  rec.ocr_done = true;
  rec.ocr_empty = !text;
  rec.needs_ocr = false;
  rec.ocr_processed_at = new Date().toISOString();

  await fsp.writeFile(jsonPath, JSON.stringify(rec, null, 2));
  console.log('[OK]', path.basename(jsonPath), 'len=', (text||'').length);
  return { ok: true };
}

// Scan all folders once
async function scanOnce() {
  let ok=0, skip=0, err=0;

  for (const folder of FOLDERS_TO_CHECK) {
    const dir = path.join(QUEUE_ROOT, folder);

    let files=[];
    try {
      files = await fsp.readdir(dir);
    } catch {
      continue;
    }

    for (const f of files) {
      if (!f.endsWith('.json')) continue;
      const p = path.join(dir, f);

      try {
        const r = await processJsonFile(p);
        if (r && r.ok) ok++; else skip++;
      } catch (e) {
        err++;
        console.error('[OCR-ERR]', p, e.message);
      }
    }
  }

  console.log(`[SCAN] ok=${ok} skip=${skip} err=${err}`);
}

// Main loop
async function main() {
  console.log('================================');
  console.log('OCR Processor Starting...');
  console.log('================================');
  console.log(`Vision API: ${visionClient ? 'ENABLED' : 'DISABLED'}`);
  console.log(`Scan interval: ${SCAN_INTERVAL_MS}ms`);
  console.log(`Folders: ${FOLDERS_TO_CHECK.join(', ')}`);
  console.log('================================');

  while (true) {
    await scanOnce().catch(e => console.error('[SCAN-LOOP]', e.message));
    await new Promise(r => setTimeout(r, SCAN_INTERVAL_MS));
  }
}

if (require.main === module) {
  main().catch(e => { console.error('[FATAL]', e); process.exit(1); });
}

module.exports = { ocrPipeline, resolveImagePath };