import os
from typing import Optional

import requests

from ..config_loader import ConfigLoader


class TelegramNotifier:
    def __init__(self, config_loader: Optional[ConfigLoader] = None) -> None:
        self._config_loader = config_loader or ConfigLoader()
        cfg = self._config_loader.load()
        telegram_cfg = cfg.get("telegram", {})
        self._bot_token: str = telegram_cfg.get("botToken", "")
        self._chat_id: str = telegram_cfg.get("chatID", "")

    def is_configured(self) -> bool:
        return bool(self._bot_token and self._chat_id)

    def send_message(self, text: str) -> None:
        if not self.is_configured():
            return
        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {"chat_id": self._chat_id, "text": text}
        # Best-effort; ignore network errors for now.
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception:
            pass
