import os, json, requests
from tenacity import retry, stop_after_attempt, wait_exponential

class RateLimitError(RuntimeError):
    def __init__(self, retry_after: float, message="Rate limited"):
        super().__init__(message)
        self.retry_after = retry_after

class DiscordSender:
    def __init__(self, config: dict = None, logger=None):
        self.config = config or {}
        self.logger = logger
        self.bot_token = os.getenv("DISCORD_BOT_TOKEN_FREE", "").strip()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=30))
    def send_webhook(self, webhook_env: str, content: str, file_path: str|None=None):
        url = os.getenv(webhook_env, "").strip()
        if not url:
            raise RuntimeError(f"Missing webhook env: {webhook_env}")
        files = None
        data = {"content": content or ""}
        headers = {}
        if file_path and os.path.exists(file_path):
            files = {"file": open(file_path, "rb")}
        r = requests.post(url, data=data, files=files, headers=headers, timeout=30)
        if r.status_code == 429:
            ra = r.headers.get("Retry-After") or "1"
            try:
                retry_after = float(ra)
            except Exception:
                retry_after = 1.0
            raise RateLimitError(retry_after, f"Rate limited: {retry_after}s")
        if r.status_code >= 300:
            raise RuntimeError(f"Webhook send failed: {r.status_code} {r.text[:200]}")
        return r.json() if r.text else {}

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=30))
    def send_bot_message(self, channel_id: str, content: str, file_path: str|None=None):
        if not self.bot_token:
            raise RuntimeError("Missing DISCORD_BOT_TOKEN_FREE")
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
        }
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                files = {"files[0]": (os.path.basename(file_path), f)}
                data = {"content": content or ""}
                r = requests.post(url, headers=headers, data=data, files=files, timeout=30)
        else:
            json_payload = {"content": content or ""}
            headers["Content-Type"] = "application/json"
            r = requests.post(url, headers=headers, data=json.dumps(json_payload), timeout=30)

        if r.status_code == 429:
            ra = r.headers.get("Retry-After") or "1"
            try:
                retry_after = float(ra)
            except Exception:
                retry_after = 1.0
            raise RateLimitError(retry_after, f"Rate limited: {retry_after}s")
        if r.status_code >= 300:
            raise RuntimeError(f"Bot send failed: {r.status_code} {r.text[:200]}")
        return r.json()

    def format_telegram_message(self, tg_data: dict) -> str:
        """Format Telegram message for Discord"""
        parts = []
        if tg_data.get("chat_title"):
            parts.append(f"**From:** {tg_data['chat_title']}")
        if tg_data.get("text"):
            parts.append(tg_data["text"][:1900])
        return "\n".join(parts) if parts else ""