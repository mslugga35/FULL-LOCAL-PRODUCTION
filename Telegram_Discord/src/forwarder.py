import os, time, json, yaml, glob, shutil
from pathlib import Path
from dotenv import load_dotenv
from src.utils.logger import setup_logger
from src.utils.discord_client import DiscordSender, RateLimitError
from src.utils.signal_client import SignalSender, SignalRateLimitError
from src.utils.picks_formatter import format_clean_picks
from src.utils.ocr import extract_text_from_image

def project_root():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.normpath(os.path.join(here, os.pardir, ""))

def main():
    root = project_root()
    load_dotenv(os.path.join(root, ".env"))

    with open(os.path.join(root, "config", "settings.yaml"), "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    with open(os.path.join(root, "config", "discord_targets.yaml"), "r", encoding="utf-8") as f:
        targets = yaml.safe_load(f)

    logs = settings["paths"]["logs"]
    queue_base = settings["paths"]["queue"]
    archive_base = settings["paths"]["archive"]
    os.makedirs(archive_base, exist_ok=True)

    logger = setup_logger("forwarder", "forwarder.log")
    discord_sender = DiscordSender(targets, logger=logger)
    signal_sender = SignalSender(targets, logger=logger)

    ocr_queues = set(settings.get("ocr", {}).get("queues", []) or [])

    fw = settings.get("forwarder", {})
    limits = fw.get("per_queue_min_interval_seconds", {})
    default_gap = float(limits.get("default", 0.5))
    on_429_cooldown = float(fw.get("on_429_cooldown_seconds", 30))
    max_retry_after = float(fw.get("max_retry_after_seconds", 60))

    last_sent = {}
    cooldown_until = {}

    logger.info("=" * 60)
    logger.info("Forwarder started with rate limiting")
    logger.info(f"Queue base: {queue_base}")
    logger.info(f"Rate limits: {limits}")
    logger.info(f"429 cooldown: {on_429_cooldown}s")
    logger.info("=" * 60)

    while True:
        made_progress = False
        now = time.time()

        for queue, cfg in targets.items():
            qdir = os.path.join(queue_base, queue)
            if not os.path.isdir(qdir):
                continue

            # Check cooldown
            if cooldown_until.get(queue, 0) > now:
                remaining = cooldown_until[queue] - now
                if remaining > 10:  # Only log if significant time remains
                    logger.debug(f"Queue {queue} in cooldown for {remaining:.0f}s")
                continue

            # Check spacing
            gap = float(limits.get(queue, default_gap))
            if now - last_sent.get(queue, 0) < gap:
                continue

            files = glob.glob(os.path.join(qdir, "*.json"))
            if not files:
                continue
            files.sort()

            path = files[0]
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content_raw = data.get("text") or ""
                file_path = data.get("media_path")
                transport = cfg.get("transport")

                # Check if we should use OCR for this queue
                if queue in ocr_queues and file_path and os.path.exists(file_path):
                    try:
                        ocr_text = extract_text_from_image(file_path)
                        label = f"{data.get('chat_title', 'Unknown')}"
                        formatted = format_clean_picks(label, content_raw, ocr_text or "")
                        # Don't send image for OCR queues
                        file_path = None
                    except Exception as e:
                        logger.warning(f"OCR failed for {queue}: {e}")
                        if transport == "signal":
                            formatted = signal_sender.format_telegram_message(data)
                        else:
                            formatted = discord_sender.format_telegram_message(data)
                else:
                    if transport == "signal":
                        formatted = signal_sender.format_telegram_message(data)
                    else:
                        formatted = discord_sender.format_telegram_message(data)

                # Send based on transport type
                if transport == "webhook":
                    discord_sender.send_webhook(cfg.get("webhook_env"), formatted, file_path)
                elif transport == "signal":
                    recipient_id = cfg.get("recipient_id")
                    signal_sender.send_message(recipient_id, formatted, file_path)
                else:
                    channel_id = str(cfg.get("channel_id"))
                    discord_sender.send_bot_message(channel_id, formatted, file_path)

                # Success - archive and update timers
                last_sent[queue] = time.time()
                ymd = time.strftime("%Y%m%d")
                dest = os.path.join(archive_base, ymd, queue)
                os.makedirs(dest, exist_ok=True)
                shutil.move(path, os.path.join(dest, os.path.basename(path)))
                logger.info(f"Sent {queue}/{os.path.basename(path)}")
                made_progress = True

            except (RateLimitError, SignalRateLimitError) as rl:
                retry_after = min(float(getattr(rl, "retry_after", 1.0)), max_retry_after)
                pause = max(retry_after, on_429_cooldown)
                cooldown_until[queue] = time.time() + pause
                logger.warning(f"Rate limit {queue}: cooling for {pause:.0f}s")

            except Exception as e:
                # Check if it's a wrapped rate limit error from tenacity
                if "RetryError" in str(type(e)) or "RateLimitError" in str(e):
                    cooldown_until[queue] = time.time() + on_429_cooldown
                    logger.warning(f"Rate limit {queue}: cooling for {on_429_cooldown}s")
                else:
                    logger.error(f"Error sending {path}: {e}")
                    # Move to failed folder
                    failed_dir = os.path.join(qdir, "failed")
                    os.makedirs(failed_dir, exist_ok=True)
                    try:
                        shutil.move(path, os.path.join(failed_dir, os.path.basename(path)))
                    except:
                        pass

        if not made_progress:
            time.sleep(0.5)

if __name__ == "__main__":
    main()