import os
import time
import json
import yaml
import glob
import shutil
import sqlite3
import threading
from pathlib import Path
from dotenv import load_dotenv

from src.utils.logger import setup_logger
from src.utils.picks_formatter import format_clean_picks
from src.utils.ocr import extract_text_from_image

# Global variables for Google Docs export
_gdocs_export_lock = threading.Lock()
_gdocs_last_export = 0
_gdocs_export_debounce = 3  # Wait 3 seconds before triggering export

# --- Discord (sender + rate-limit shim) ---
from src.utils.discord_client import DiscordSender
try:
    from src.utils.discord_client import RateLimitError  # preferred/new
except Exception:
    try:
        from src.utils.discord_client import RateLimitException as RateLimitError  # old name
    except Exception:
        class RateLimitError(Exception):  # last-resort fallback
            pass


def project_root():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.normpath(os.path.join(here, os.pardir, ""))


def setup_idempotency_db(root):
    """
    Initialize SQLite database for tracking sent messages to prevent duplicates

    Returns:
        sqlite3.Connection: Database connection
    """
    state_dir = os.path.join(root, "state")
    os.makedirs(state_dir, exist_ok=True)

    db_path = os.path.join(state_dir, "forwarder.sqlite3")
    db = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA temp_store=MEMORY")
    db.execute("PRAGMA auto_vacuum=INCREMENTAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS sent (
            chat_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (chat_id, message_id)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_sent_at ON sent(sent_at)")
    db.commit()
    return db


def purge_old(db, logger=None):
    """Remove entries older than 24 hours to prevent unbounded growth"""
    try:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute("DELETE FROM sent WHERE sent_at < datetime('now','-1 day')")
        deleted = cursor.rowcount
        db.execute("COMMIT")
        db.execute("PRAGMA incremental_vacuum(200)")
        if logger and deleted > 0:
            logger.info(f"TTL purge: removed {deleted} entries older than 24h")
    except Exception as e:
        if logger:
            logger.warning(f"TTL purge failed: {e}")


def ttl_loop(db, logger=None, interval_seconds=3600):
    """Background thread to purge old entries every hour"""
    while True:
        time.sleep(interval_seconds)
        purge_old(db, logger)


def derive_label(data: dict, cfg: dict) -> str:
    """
    Choose a nice display label. Priority:
      chat_title -> from_name -> from_username -> username -> targets.yaml label/name -> "Unknown"
    """
    return (
        data.get("chat_title")
        or data.get("from_name")
        or data.get("from_username")
        or data.get("username")
        or cfg.get("label")
        or cfg.get("name")
        or "Unknown"
    )


def _run_gdocs_export():
    """Background thread to run Google Docs export"""
    global _gdocs_last_export
    try:
        import subprocess
        import sys

        # Get the path to the export script
        here = os.path.abspath(os.path.dirname(__file__))
        root = os.path.normpath(os.path.join(here, os.pardir))
        venv_python = os.path.join(root, ".venv", "Scripts", "python.exe")
        export_script = os.path.join(root, "src", "export_to_gdocs.py")

        # Run the export in a subprocess (non-blocking)
        subprocess.Popen(
            [venv_python, export_script],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        _gdocs_last_export = time.time()
    except Exception as e:
        pass  # Silently fail - export runs in background thread


def trigger_gdocs_export():
    """
    Trigger Google Docs export with debouncing.
    Only exports if at least 3 seconds have passed since last export.
    Runs in background thread to avoid blocking the forwarder.
    """
    global _gdocs_last_export

    with _gdocs_export_lock:
        now = time.time()
        if now - _gdocs_last_export >= _gdocs_export_debounce:
            # Start export in background thread
            thread = threading.Thread(target=_run_gdocs_export, daemon=True)
            thread.start()


def main():
    root = project_root()
    load_dotenv(os.path.join(root, ".env"))

    with open(os.path.join(root, "config", "settings.yaml"), "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    with open(os.path.join(root, "config", "discord_targets.yaml"), "r", encoding="utf-8") as f:
        targets = yaml.safe_load(f)

    queue_base = settings["paths"]["queue"]
    archive_base = settings["paths"]["archive"]
    os.makedirs(archive_base, exist_ok=True)

    logger = setup_logger("forwarder", "forwarder.log")
    discord = DiscordSender(targets, logger=logger)

    # Initialize idempotency database
    db = setup_idempotency_db(root)
    logger.info("Idempotency database initialized")

    # One-shot cleanup of old entries
    purge_old(db, logger)

    # Start background TTL cleanup thread (runs every hour)
    threading.Thread(target=ttl_loop, args=(db, logger), daemon=True).start()
    logger.info("TTL cleanup thread started (purges entries older than 24h every hour)")

    # Queues that should run OCR when an image is present (FREE side only)
    ocr_queues = set(settings.get("ocr", {}).get("queues", []) or [])

    fw = settings.get("forwarder", {})
    limits = fw.get("per_channel_min_interval_seconds", {})
    default_gap = float(limits.get("default", 1.0))
    on_429_cooldown = float(fw.get("on_429_cooldown_seconds", 90))
    max_retry_after = float(fw.get("max_retry_after_seconds", 300))

    last_sent_channel = {}  # Track by channel_id, not queue
    cooldown_until_channel = {}  # Track by channel_id

    # Rate limit loop detection
    rate_limit_consecutive = {}  # Track consecutive rate limits per channel
    rate_limit_timestamps = {}  # Track when rate limits occur for loop detection
    LOOP_DETECTION_WINDOW = 600  # 10 minutes in seconds
    LOOP_THRESHOLD = 5  # Alert after 5 rate limits in the window

    # Map queues to channels for rate limiting
    queue_to_channel = {}
    for queue, cfg in targets.items():
        channel_id = str(cfg.get("channel_id", ""))
        if channel_id:
            queue_to_channel[queue] = channel_id

    logger.info("=" * 60)
    logger.info("Forwarder started with channel-based rate limiting")
    logger.info(f"Queue base: {queue_base}")
    logger.info(f"Channel rate limits: {limits}")
    logger.info(f"429 cooldown: {on_429_cooldown}s")
    logger.info("=" * 60)

    while True:
        made_progress = False
        now = time.time()

        for queue, cfg in targets.items():
            qdir = os.path.join(queue_base, queue)
            if not os.path.isdir(qdir):
                continue

            # Get channel for this queue
            channel_id = queue_to_channel.get(queue)
            if not channel_id:
                continue

            # Cooldown after a 429 (per channel)
            if cooldown_until_channel.get(channel_id, 0) > now:
                continue

            # Respect per-channel spacing
            gap = float(limits.get(channel_id, default_gap))
            if now - last_sent_channel.get(channel_id, 0) < gap:
                continue

            files = sorted(glob.glob(os.path.join(qdir, "*.json")))
            if not files:
                continue

            path = files[0]

            # ATOMIC CLAIM: Move to _processing before reading to prevent concurrent sends
            processing_dir = os.path.join(qdir, "_processing")
            os.makedirs(processing_dir, exist_ok=True)

            src_path = Path(path)
            claimed_path = os.path.join(processing_dir, src_path.name)

            try:
                os.replace(path, claimed_path)  # Atomic on NTFS
            except FileNotFoundError:
                # Another forwarder already claimed it
                continue
            except Exception as e:
                logger.warning(f"Failed to claim {src_path.name}: {e}")
                continue

            # Now work with the claimed file
            try:
                with open(claimed_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract message identifiers for idempotency check
                chat_id = str(data.get("chat_id", ""))
                message_id = int(data.get("id", 0)) if data.get("id") else 0

                # Check if already sent (but don't insert yet - do that after successful send)
                # Skip duplicate check if allow_duplicates is True for this queue
                allow_duplicates = cfg.get("allow_duplicates", False)
                if chat_id and message_id and not allow_duplicates:
                    cur = db.cursor()
                    cur.execute("SELECT 1 FROM sent WHERE chat_id=? AND message_id=?", (chat_id, message_id))
                    if cur.fetchone():
                        # Already sent - move to duplicates
                        duplicates_dir = os.path.join(archive_base, time.strftime("%Y%m%d"), queue, "duplicates")
                        os.makedirs(duplicates_dir, exist_ok=True)
                        shutil.move(claimed_path, os.path.join(duplicates_dir, src_path.name))
                        logger.info(f"⚠️ Skipped duplicate: {queue}/{src_path.name} ({chat_id}_{message_id})")
                        made_progress = True
                        continue

                content_raw = (data.get("text") or "").strip()
                file_path = data.get("media_path")
                transport = (cfg.get("transport") or "").lower()  # 'webhook' or default(bot)
                label = derive_label(data, cfg)

                # Check file size - Discord bot limit is 8MB (25MB for nitro servers, but play it safe)
                MAX_FILE_SIZE = 8 * 1024 * 1024  # 8MB in bytes
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    if file_size > MAX_FILE_SIZE:
                        logger.warning(f"Skipping oversized file ({file_size / 1024 / 1024:.1f}MB > 8MB): {os.path.basename(file_path)}")
                        oversized_dir = os.path.join(qdir, "oversized")
                        os.makedirs(oversized_dir, exist_ok=True)
                        shutil.move(claimed_path, os.path.join(oversized_dir, src_path.name))
                        made_progress = True
                        continue

                # --- Format based on queue tier ---
                if queue in ("paid_uatb", "paid_diamond", "paid_new_channel"):
                    # PAID: allow media; if no text, just show the label (no placeholder line)
                    if content_raw:
                        formatted = f"**{label}**\n{content_raw}"
                    else:
                        formatted = f"**{label}**"
                    # keep file_path as-is so image/video gets sent
                else:
                    # FREE: text-only. Prefer OCR text if configured for this queue.
                    if queue in ocr_queues and file_path and os.path.exists(file_path):
                        try:
                            ocr_text = extract_text_from_image(file_path) or ""
                        except Exception as e:
                            logger.warning(f"OCR failed for {queue}: {e}")
                            ocr_text = ""
                    else:
                        ocr_text = ""
                    # FREE posts omit the bold label and focus on clean picks text
                    # Enable dedup checking for FREE channels
                    formatted = format_clean_picks("", content_raw, ocr_text, check_dedup=True)
                    file_path = None  # enforce text-only on FREE

                # Skip if formatter returned None (recap or duplicate)
                if formatted is None:
                    skipped_dir = os.path.join(archive_base, time.strftime("%Y%m%d"), queue, "skipped")
                    os.makedirs(skipped_dir, exist_ok=True)
                    shutil.move(claimed_path, os.path.join(skipped_dir, src_path.name))
                    logger.info(f"⏭️ Skipped (recap/duplicate): {queue}/{src_path.name}")
                    made_progress = True
                    continue

                # --- Send to Discord ---
                if transport == "webhook":
                    discord.send_webhook(cfg.get("webhook_env"), formatted, file_path)
                else:
                    channel_id = str(cfg.get("channel_id"))
                    discord.send_bot_message(channel_id, formatted, file_path)

                # SUCCESS - Now record in database to prevent future duplicates
                if chat_id and message_id:
                    try:
                        cur = db.cursor()
                        cur.execute("INSERT INTO sent(chat_id, message_id) VALUES (?,?)", (chat_id, message_id))
                        db.commit()
                    except sqlite3.IntegrityError:
                        # Race condition - another forwarder just sent this. Log but continue archiving.
                        logger.warning(f"Race: Message {chat_id}_{message_id} was sent by another forwarder")

                # Success: record timing by CHANNEL, log, small delay, archive
                last_sent_channel[channel_id] = time.time()
                # Reset rate limit counters on successful send
                if channel_id in rate_limit_consecutive:
                    rate_limit_consecutive[channel_id] = 0
                logger.info(f"Sent {queue}/{src_path.name} [channel: {channel_id}]")
                time.sleep(0.5)

                ymd = time.strftime("%Y%m%d")
                dest = os.path.join(archive_base, ymd, queue)
                os.makedirs(dest, exist_ok=True)
                shutil.move(claimed_path, os.path.join(dest, src_path.name))
                made_progress = True

                # Trigger Google Docs export for free channels
                if queue.startswith("free_"):
                    try:
                        trigger_gdocs_export()
                    except Exception as e:
                        logger.warning(f"Google Docs export trigger failed: {e}")

            except RateLimitError as rl:
                # Rate limited - move file back to queue for retry
                try:
                    shutil.move(claimed_path, path)
                except Exception:
                    pass  # File may already be moved or deleted

                # Respect server-provided retry_after when available but cap it
                retry_after = float(getattr(rl, "retry_after", on_429_cooldown))
                pause = max(min(retry_after, max_retry_after), on_429_cooldown)
                cooldown_until_channel[channel_id] = time.time() + pause

                # Track rate limit for loop detection
                if channel_id not in rate_limit_consecutive:
                    rate_limit_consecutive[channel_id] = 0
                    rate_limit_timestamps[channel_id] = []

                rate_limit_consecutive[channel_id] += 1
                rate_limit_timestamps[channel_id].append(now)

                # Clean old timestamps outside detection window
                rate_limit_timestamps[channel_id] = [
                    t for t in rate_limit_timestamps[channel_id]
                    if now - t < LOOP_DETECTION_WINDOW
                ]

                # Check for rate limit loop pattern
                recent_count = len(rate_limit_timestamps[channel_id])
                if recent_count >= LOOP_THRESHOLD:
                    queue_files = len(glob.glob(os.path.join(qdir, "*.json")))
                    logger.critical(
                        f"⚠️ RATE LIMIT LOOP DETECTED ⚠️\n"
                        f"Channel: {channel_id}\n"
                        f"Queue: {queue}\n"
                        f"Rate limits: {recent_count} in last {LOOP_DETECTION_WINDOW/60:.0f} minutes\n"
                        f"Messages pending: {queue_files}\n"
                        f"Action: Consider archiving old messages or increasing cooldown"
                    )

                logger.warning(f"Rate limit {queue} (channel {channel_id}): cooling for {pause:.0f}s [{rate_limit_consecutive[channel_id]} consecutive]")

            except Exception as e:
                et = str(type(e))
                if "RetryError" in et or "RateLimitError" in et:
                    # Rate limit error - move file back to queue for retry
                    try:
                        shutil.move(claimed_path, path)
                    except Exception:
                        pass

                    cooldown_until_channel[channel_id] = time.time() + on_429_cooldown

                    # Track rate limit for loop detection
                    if channel_id not in rate_limit_consecutive:
                        rate_limit_consecutive[channel_id] = 0
                        rate_limit_timestamps[channel_id] = []

                    rate_limit_consecutive[channel_id] += 1
                    rate_limit_timestamps[channel_id].append(now)

                    # Clean old timestamps outside detection window
                    rate_limit_timestamps[channel_id] = [
                        t for t in rate_limit_timestamps[channel_id]
                        if now - t < LOOP_DETECTION_WINDOW
                    ]

                    # Check for rate limit loop pattern
                    recent_count = len(rate_limit_timestamps[channel_id])
                    if recent_count >= LOOP_THRESHOLD:
                        queue_files = len(glob.glob(os.path.join(qdir, "*.json")))
                        logger.critical(
                            f"⚠️ RATE LIMIT LOOP DETECTED ⚠️\n"
                            f"Channel: {channel_id}\n"
                            f"Queue: {queue}\n"
                            f"Rate limits: {recent_count} in last {LOOP_DETECTION_WINDOW/60:.0f} minutes\n"
                            f"Messages pending: {queue_files}\n"
                            f"Action: Consider archiving old messages or increasing cooldown"
                        )

                    logger.warning(f"Rate limit {queue} (channel {channel_id}): cooling for {on_429_cooldown:.0f}s [{rate_limit_consecutive[channel_id]} consecutive]")
                else:
                    # Other error - move to failed folder
                    if os.path.exists(claimed_path):
                        logger.error(f"Error sending {src_path.name}: {e}")
                    failed_dir = os.path.join(qdir, "failed")
                    os.makedirs(failed_dir, exist_ok=True)
                    try:
                        shutil.move(claimed_path, os.path.join(failed_dir, src_path.name))
                    except Exception:
                        pass

        if not made_progress:
            time.sleep(0.5)


if __name__ == "__main__":
    main()
