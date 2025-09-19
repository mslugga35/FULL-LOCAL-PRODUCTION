
import argparse, os, yaml
from dotenv import load_dotenv
from src.utils.discord_client import DiscordSender

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True)
    parser.add_argument("--text", default="Hello from test_forward")
    parser.add_argument("--file", default=None)
    args = parser.parse_args()

    base = os.getcwd()  # expect to run from install path
    load_dotenv(os.path.join(base, ".env"))
    with open(os.path.join(base, "config", "discord_targets.yaml"), "r", encoding="utf-8") as f:
        targets = yaml.safe_load(f)

    cfg = targets.get(args.queue)
    if not cfg:
        print(f"Unknown queue: {args.queue}")
        return

    sender = DiscordSender(targets)
    if cfg.get("transport") == "webhook":
        envname = cfg.get("webhook_env")
        print(sender.send_webhook(envname, args.text, args.file))
    else:
        print(sender.send_bot_message(str(cfg.get("channel_id")), args.text, args.file))

if __name__ == "__main__":
    main()
