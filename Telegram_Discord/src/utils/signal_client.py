import os, json, requests, subprocess
from tenacity import retry, stop_after_attempt, wait_exponential

class SignalRateLimitError(RuntimeError):
    def __init__(self, retry_after: float, message="Signal rate limited"):
        super().__init__(message)
        self.retry_after = retry_after

class SignalSender:
    def __init__(self, config: dict = None, logger=None):
        self.config = config or {}
        self.logger = logger
        self.signal_cli_path = os.getenv("SIGNAL_CLI_PATH", "signal-cli")
        self.signal_number = os.getenv("SIGNAL_PHONE_NUMBER", "").strip()
        
    def log(self, level, msg):
        if self.logger:
            getattr(self.logger, level)(msg)
        else:
            print(f"[{level.upper()}] {msg}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=1, max=10))
    def send_signal_message(self, recipient_id: str, content: str, file_path: str = None):
        """Send message via Signal CLI"""
        if not self.signal_number:
            raise RuntimeError("SIGNAL_PHONE_NUMBER not configured")
            
        if not recipient_id:
            raise RuntimeError("Signal recipient ID/group ID required")
            
        try:
            cmd = [
                self.signal_cli_path,
                "-a", self.signal_number,
                "send",
                "-g" if recipient_id.startswith("group.") else "-",
                recipient_id if recipient_id.startswith("group.") else recipient_id,
                "-m", content or ""
            ]
            
            # Add attachment if provided
            if file_path and os.path.exists(file_path):
                cmd.extend(["-a", file_path])
                
            self.log("debug", f"Running Signal CLI: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = f"Signal CLI failed: {result.stderr}"
                self.log("error", error_msg)
                raise RuntimeError(error_msg)
                
            self.log("debug", f"Signal message sent successfully to {recipient_id}")
            return True
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Signal CLI timeout")
        except Exception as e:
            self.log("error", f"Signal send error: {e}")
            raise

    def send_via_rest_api(self, recipient_id: str, content: str, file_path: str = None):
        """Send via Signal REST API (if available)"""
        api_url = os.getenv("SIGNAL_API_URL", "").strip()
        api_token = os.getenv("SIGNAL_API_TOKEN", "").strip()
        
        if not api_url or not api_token:
            raise RuntimeError("Signal REST API not configured")
            
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "number": self.signal_number,
            "recipients": [recipient_id],
            "message": content or ""
        }
        
        # Handle file attachment for REST API
        if file_path and os.path.exists(file_path):
            # Note: File upload for Signal REST API would need additional implementation
            # This is a placeholder for when REST API supports file uploads
            payload["attachment"] = file_path
            
        try:
            response = requests.post(
                f"{api_url}/v2/send",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", "1"))
                raise SignalRateLimitError(retry_after)
                
            if response.status_code >= 400:
                error_msg = f"Signal API error {response.status_code}: {response.text}"
                self.log("error", error_msg)
                raise RuntimeError(error_msg)
                
            self.log("debug", f"Signal message sent via REST API to {recipient_id}")
            return True
            
        except requests.RequestException as e:
            self.log("error", f"Signal REST API error: {e}")
            raise

    def send_message(self, recipient_id: str, content: str, file_path: str = None):
        """Main method to send Signal message - tries REST API first, falls back to CLI"""
        try:
            # Try REST API first if configured
            if os.getenv("SIGNAL_API_URL") and os.getenv("SIGNAL_API_TOKEN"):
                return self.send_via_rest_api(recipient_id, content, file_path)
            else:
                # Fall back to Signal CLI
                return self.send_signal_message(recipient_id, content, file_path)
        except Exception as e:
            self.log("error", f"Failed to send Signal message: {e}")
            raise

    def format_telegram_message(self, data: dict) -> str:
        """Format Telegram message for Signal (similar to Discord client)"""
        chat_title = data.get("chat_title", "Unknown")
        sender = data.get("sender_name", "Unknown")
        text = data.get("text", "")
        timestamp = data.get("timestamp", "")
        
        if text:
            return f"**{chat_title}**\n{sender}: {text}"
        else:
            return f"**{chat_title}**\n{sender}: [Media]"