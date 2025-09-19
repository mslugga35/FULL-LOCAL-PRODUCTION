#!/usr/bin/env node
// config-auditor.js
// Snapshots + diffs critical files so you can see EXACT changes any time.

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

require('dotenv').config({ path: '/root/bots/.env' });
const MONITOR_WEBHOOK = process.env.MONITOR_WEBHOOK || '';

const WATCH = [
  '/root/bots/.env',
  '/root/bots/discord_sender.js',
  '/root/bots/forwarder.py',
  '/root/python/telegram_to_discord.py',
  '/root/bots/message_router.js',
  '/root/bots/ocr_processor.js',
  '/root/bots/paid_webhook_sender.js',
  '/root/bots/watchdog-pro.js',
];

const SNAP_DIR = '/root/bots/_snapshots';
const REPORT_DIR = '/root/bots/_audits';

function sha256(buf) { return crypto.createHash('sha256').update(buf).digest('hex'); }
function read(p){ try { return fs.readFileSync(p,'utf8'); } catch { return null; } }

function diffUnified(aStr, bStr) {
  // Minimal inline diff to avoid external deps (simple, line-based)
  const a = (aStr||'').split('\n'), b = (bStr||'').split('\n');
  const out = [];
  out.push('--- old');
  out.push('+++ new');
  const max = Math.max(a.length, b.length);
  for (let i=0;i<max;i++){
    const aa = a[i] ?? '';
    const bb = b[i] ?? '';
    if (aa === bb) continue;
    out.push(`- ${aa}`);
    out.push(`+ ${bb}`);
  }
  return out.join('\n');
}

async function alert(content) {
  if (!MONITOR_WEBHOOK) return;
  try {
    await fetch(MONITOR_WEBHOOK, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ content: content.slice(0, 1900) }),
    });
  } catch {}
}

function ensure(p){ if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true }); }

(async () => {
  ensure(SNAP_DIR); ensure(REPORT_DIR);
  const stamp = new Date().toISOString().replace(/[:.]/g,'-');
  let report = [`[${stamp}] CONFIG AUDIT`];

  for (const file of WATCH) {
    const base = path.basename(file);
    const cur = read(file);
    if (cur === null) {
      report.push(`❌ missing: ${file}`);
      continue;
    }
    const snapPath = path.join(SNAP_DIR, base);
    const prev = read(snapPath);
    const curHash = sha256(cur);
    if (prev === null) {
      fs.writeFileSync(snapPath, cur);
      report.push(`🆕 baseline: ${base} (${curHash.slice(0,12)})`);
    } else {
      const prevHash = sha256(prev);
      if (prevHash !== curHash) {
        const d = diffUnified(prev, cur);
        fs.writeFileSync(snapPath, cur);
        report.push(`✏️  changed: ${base}\n${d}`);
      } else {
        report.push(`✓ unchanged: ${base} (${curHash.slice(0,12)})`);
      }
    }
  }

  const body = report.join('\n');
  const out = path.join(REPORT_DIR, `${stamp}.txt`);
  fs.writeFileSync(out, body);
  console.log(body);
  await alert(`Config audit created: ${out}\n\n${body.substring(0,1200)}`);
})();