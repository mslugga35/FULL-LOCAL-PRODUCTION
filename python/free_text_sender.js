const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Discord webhooks - REPLACE WITH YOUR ACTUAL WEBHOOKS
const QUEUES = [
  {
    dir: '/root/bots/message_queue/free_cappers',
    label: 'FREE CAPPERS',
    webhook: 'https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE'
  },
  {
    dir: '/root/bots/message_queue/leaked_cappers',
    label: 'CAPPERS LEAKED',
    webhook: 'https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE'
  },
  {
    dir: '/root/bots/message_queue/exclusive_cappers',
    label: 'EXCLUSIVE CAPPERS',
    webhook: 'https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE'
  }
];

const PROCESSED = '/root/bots/message_queue/processed';
const POLL_MS = 2000;

async function send(webhook, content) {
  try {
    const res = await axios.post(webhook, {
      content,
      username: 'Free Picks Bot',
      allowed_mentions: { parse: [] }
    });
    return true;
  } catch (error) {
    if (error.response && error.response.status === 429) {
      const retryAfter = error.response.data.retry_after || 1;
      console.log(`[free-sender] Rate limited, waiting ${retryAfter}s`);
      await new Promise(r => setTimeout(r, retryAfter * 1000));
      return send(webhook, content);
    }
    console.error('[free-sender] Send failed:', error.message);
    return false;
  }
}

function listCleanFiles(dir) {
  try {
    return fs.readdirSync(dir).filter(f => f.endsWith('.clean.txt')).sort();
  } catch {
    return [];
  }
}

async function processQueue(q) {
  if (q.webhook.includes('YOUR_WEBHOOK_HERE')) {
    return;
  }

  const files = listCleanFiles(q.dir);

  for (const f of files) {
    const p = path.join(q.dir, f);
    const text = fs.readFileSync(p, 'utf-8').trim();
    const msg = text.length > 1900 ? text.slice(0, 1900) + '\n...' : text;

    try {
      const sent = await send(q.webhook, msg);
      if (sent) {
        const base = f.replace('.clean.txt', '');
        const outdir = path.join(PROCESSED, path.basename(q.dir));
        fs.mkdirSync(outdir, { recursive: true });

        for (const name of fs.readdirSync(q.dir)) {
          if (name.startsWith(base)) {
            const src = path.join(q.dir, name);
            const dst = path.join(outdir, name);
            try {
              fs.renameSync(src, dst);
            } catch {
              try {
                fs.copyFileSync(src, dst);
                fs.unlinkSync(src);
              } catch {}
            }
          }
        }
        console.log(`[free-sender] Sent ${f} to Discord`);
      }
    } catch (e) {
      console.error('[free-sender] Error:', e.message);
      await new Promise(r => setTimeout(r, 2000));
    }
  }
}

async function main() {
  console.log('=== Free Text Sender Started ===');
  console.log('Monitoring:', QUEUES.map(q => path.basename(q.dir)).join(', '));

  for (const q of QUEUES) {
    fs.mkdirSync(q.dir, { recursive: true });
  }

  setInterval(() => {
    QUEUES.forEach(processQueue);
  }, POLL_MS);
}

main().catch(console.error);
