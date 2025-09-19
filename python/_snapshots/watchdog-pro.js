#!/usr/bin/env node
// watchdog-pro.js
// Smart, functional watchdog for your pipeline.
// - Validates Discord guild & channel access with the bot token.
// - Monitors queue/inbox size & freshness.
// - Restarts targeted PM2 apps when stalled.
// - Sends alerts to a Discord webhook.
// Requires Node 18+ (global fetch). Uses the same /root/bots/.env.

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

require('dotenv').config({ path: '/root/bots/.env' });

// ---------- Config (from .env or sane defaults) ----------
const QUEUE_DIR = process.env.QUEUE_DIR || '/root/bots/message_queue';
const INBOX_DIR = process.env.INBOX_DIR || '/root/inbox';
const PROCESSED_DIR = process.env.PROCESSED_DIR || '/root/bots/processed';

const DISCORD_TOKEN =
  process.env.DISCORD_SENDER_TOKEN ||
  process.env.DISCORD_OCR_BOT_TOKEN || '';

const GUILD_ID = process.env.GUILD_ID || '1390050801136701642'; // your main server

const CH_FREE      = process.env.CH_FREE      || '1403894557615325216'; // #leaks
const CH_LEAKED    = process.env.CH_LEAKED    || '1403894596186017962'; // #cappers-leaked
const CH_EXCLUSIVE = process.env.CH_EXCLUSIVE || '1403894653660692500'; // #exclusive-cappers

const MONITOR_WEBHOOK = process.env.MONITOR_WEBHOOK || ''; // optional: a Discord webhook to receive alerts

// PM2 app names you actually run
const APPS = {
  producer:  process.env.PM2_TG_PRODUCER   || 'tg-producer',
  ocr:       process.env.PM2_OCR           || 'ocr-processor',
  sender:    process.env.PM2_SENDER        || 'discord-sender',
  router:    process.env.PM2_ROUTER        || 'message-router',
  forwarder: process.env.PM2_FORWARDER     || 'telegram-forwarder',
  paidHook:  process.env.PM2_PAID_WEBHOOK  || 'paid-webhook',
};

const LOOP_MS = 60_000;          // run every 60s
const STALE_MS = 3 * 60_000;     // "no progress" window
const LARGE_BACKLOG = 25;        // threshold per folder to trigger faster mode / restarts

// ---------- helpers ----------
function nowIso() { return new Date().toISOString(); }
function msAgo(tsMs) { return Date.now() - tsMs; }
function exists(p) { try { fs.accessSync(p); return true; } catch { return false; } }
function listJson(dir) {
  try { return fs.readdirSync(dir).filter(f => f.endsWith('.json') && f !== 'processed_today.json'); }
  catch { return []; }
}
function mtime(p) {
  try { return fs.statSync(p).mtimeMs; } catch { return 0; }
}
function findNewestFile(dir) {
  const files = listJson(dir).map(f => path.join(dir, f));
  let newest = 0;
  for (const f of files) newest = Math.max(newest, mtime(f));
  return newest;
}

async function alert(msg, extra) {
  const text = `**[Watchdog] ${nowIso()}**\n${msg}${extra ? `\n\`\`\`\n${extra}\n\`\`\`` : ''}`;
  console.log(text);
  if (!MONITOR_WEBHOOK) return;

  try {
    await fetch(MONITOR_WEBHOOK, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ content: text.substring(0, 1900) }),
    });
  } catch (e) {
    console.error('Alert webhook failed:', e.message);
  }
}

function pm2(cmd) {
  return new Promise(resolve => {
    exec(`pm2 ${cmd}`, { timeout: 20_000 }, (err, stdout, stderr) => {
      resolve({ err, stdout: stdout?.toString() || '', stderr: stderr?.toString() || '' });
    });
  });
}

async function pm2Restart(name, updateEnv = true) {
  const { stdout, stderr } = await pm2(`restart ${name}${updateEnv ? ' --update-env' : ''}`);
  await alert(`Restarted \`${name}\``, (stdout || stderr).trim());
}

function countQueue() {
  const folders = ['free_cappers', 'leaked_cappers', 'exclusive_cappers', 'paid_uatb', 'paid_diamond', 'paid_cappers'];
  const summary = {};
  for (const f of folders) {
    const dir = path.join(QUEUE_DIR, f);
    let count = 0;
    if (exists(dir)) count = listJson(dir).length;
    summary[f] = count;
  }
  return summary;
}

function newestActivitySummary() {
  const folders = ['free_cappers', 'leaked_cappers', 'exclusive_cappers', 'paid_uatb', 'paid_diamond', 'paid_cappers'];
  const lines = [];
  for (const f of folders) {
    const dir = path.join(QUEUE_DIR, f);
    const newest = exists(dir) ? findNewestFile(dir) : 0;
    const age = newest ? Math.round(msAgo(newest) / 1000) : null;
    lines.push(`${f}: newest ${age === null ? 'n/a' : age + 's'} ago`);
  }
  if (exists(INBOX_DIR)) {
    const newest = findNewestFile(INBOX_DIR);
    lines.push(`inbox: newest ${newest ? Math.round(msAgo(newest)/1000)+'s' : 'n/a'} ago`);
  }
  return lines.join('\n');
}

// ---------- Discord checks ----------
async function discordGet(pathUrl) {
  if (!DISCORD_TOKEN) return { ok: false, status: 0, text: 'no token' };
  try {
    const r = await fetch(`https://discord.com/api/v10${pathUrl}`, {
      headers: { Authorization: `Bot ${DISCORD_TOKEN}` }
    });
    const t = await r.text();
    return { ok: r.ok, status: r.status, text: t };
  } catch (e) {
    return { ok: false, status: 0, text: e.message };
  }
}

async function checkDiscordAccess() {
  const resMe = await discordGet('/users/@me');
  if (!resMe.ok) return { ok: false, reason: `token invalid? /users/@me => ${resMe.status} ${resMe.text}` };

  const guild = await discordGet(`/guilds/${GUILD_ID}`);
  if (!guild.ok) return { ok: false, reason: `Unknown Guild or no access: ${GUILD_ID} => ${guild.status}` };

  // Channels
  const checks = [
    { name: 'free', id: CH_FREE },
    { name: 'leaked', id: CH_LEAKED },
    { name: 'exclusive', id: CH_EXCLUSIVE },
  ];

  const out = [];
  let allOk = true;
  for (const c of checks) {
    const r = await discordGet(`/channels/${c.id}`);
    const ok = r.ok;
    allOk &&= ok;
    out.push(`${c.name}(${c.id}): ${ok ? 'OK' : `NO (${r.status})`}`);
  }
  return { ok: allOk, details: out.join(', ') };
}

// ---------- Staleness heuristics ----------
function lastProcessedTs() {
  const state = path.join(PROCESSED_DIR, 'processed_today.json');
  try {
    const j = JSON.parse(fs.readFileSync(state, 'utf8'));
    return mtime(state); // when it was updated last
  } catch { return 0; }
}

// ---------- Main loop ----------
let lastSummary = null;

async function runOnce() {
  try {
    // 1) PM2 health (basic)
    const jlist = await pm2('jlist');
    const online = {};
    try { JSON.parse(jlist.stdout || '[]').forEach(p => { online[p.name] = p.pm2_env?.status; }); } catch {}
    const mustHave = Object.values(APPS);
    const missing = mustHave.filter(n => online[n] !== 'online');

    if (missing.length) {
      await alert(`PM2 offline apps: ${missing.join(', ')}`);
      for (const n of missing) await pm2Restart(n, true);
    }

    // 2) Discord functional access
    const dc = await checkDiscordAccess();
    if (!dc.ok) {
      await alert(`Discord access problem: ${dc.reason || dc.details || 'unknown'}`);
      // try gentle restart of sender
      await pm2Restart(APPS.sender, true);
    }

    // 3) Backlogs + freshness
    const q = countQueue();
    const total = Object.values(q).reduce((a,b)=>a+b,0);
    const newestLines = newestActivitySummary();

    const inboxNewest = findNewestFile(INBOX_DIR);
    const processedNewest = lastProcessedTs();

    const staleInbox = inboxNewest && msAgo(inboxNewest) > STALE_MS;
    const staleProcessed = processedNewest && msAgo(processedNewest) > STALE_MS;

    let actions = [];

    // Heuristic: many image messages hang -> ocr stuck
    const likelyOcrBacklog = (q.free_cappers + q.leaked_cappers + q.exclusive_cappers) > LARGE_BACKLOG;

    if (staleInbox) {
      actions.push(`Inbox stale (${Math.round(msAgo(inboxNewest)/1000)}s) → restart ${APPS.producer}`);
      await pm2Restart(APPS.producer, true);
    }

    if (total > LARGE_BACKLOG && staleProcessed) {
      // Nothing is moving
      actions.push(`Queue ${total} and no processing in ${Math.round(msAgo(processedNewest)/1000)}s → restart ${APPS.sender}`);
      await pm2Restart(APPS.sender, true);
    } else if (likelyOcrBacklog && !staleProcessed) {
      // OCR may be the bottleneck; scale OCR temporarily
      actions.push(`OCR backlog suspected (free/leaked/exclusive=${q.free_cappers+q.leaked_cappers+q.exclusive_cappers})`);
      // Optional: set BACKLOG_FAST to speed sender
      await pm2(`restart ${APPS.ocr}`);
    }

    // 4) Optional: fast mode when backlog large
    if (total > LARGE_BACKLOG) {
      process.env.BACKLOG_FAST = '1';
      await pm2Restart(APPS.sender, true);
      actions.push('Enabled BACKLOG_FAST for sender');
    }

    // 5) One compact status line
    const summary =
      `PM2: ${mustHave.map(n => `${n}:${online[n]||'down'}`).join(' ')} | ` +
      `Queue: ${Object.entries(q).map(([k,v])=>`${k}=${v}`).join(' ')} | ` +
      `Discord: ${dc.details || dc.reason || 'ok'}`;

    if (summary !== lastSummary) {
      await alert(summary, newestLines + (actions.length ? `\nACTIONS: ${actions.join(' | ')}` : ''));
      lastSummary = summary;
    }
  } catch (e) {
    await alert(`Watchdog crash: ${e.message}`);
  }
}

(async () => {
  await runOnce();
  setInterval(runOnce, LOOP_MS);
})();