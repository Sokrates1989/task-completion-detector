"""Send Telegram text/photos without exposing credentials or transport errors."""

from io import BytesIO
from typing import Optional

import requests
from PIL import Image

from ..config_loader import ConfigLoader


class TelegramNotifier:
    """Use the locally configured Telegram bot and destination chat."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None) -> None:
        self._config_loader = config_loader or ConfigLoader()
        cfg = self._config_loader.load()
        telegram_cfg = cfg.get("telegram", {})
        self._bot_token: str = telegram_cfg.get("botToken", "")
        self._chat_id: str = telegram_cfg.get("chatID", "")

    def is_configured(self) -> bool:
        """Return whether the bot token and destination chat are present."""
        return bool(self._bot_token and self._chat_id)

    def send_message(self, text: str) -> bool:
        """Return whether Telegram accepted the text, using a ten-second timeout.

        Missing credentials, HTTP/API errors, malformed responses and transport
        failures return False. This confirms API acceptance, not that a person
        has received or read the message.
        """
        if not self.is_configured():
            return False
        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {"chat_id": self._chat_id, "text": text}
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            return isinstance(result, dict) and result.get("ok") is True
        except (requests.RequestException, ValueError):
            return False

    def send_photo(self, image: Optional[Image.Image], caption: Optional[str] = None) -> bool:
        """Return whether Telegram accepted a PNG screenshot and optional caption.

        Missing credentials/image, encoding failures, malformed responses and
        transport/API errors return False. The upload buffer closes on every
        path; the caller retains ownership of the image. Requests use the same
        ten-second timeout as text messages.
        """
        if not self.is_configured() or image is None:
            return False
        url = f"https://api.telegram.org/bot{self._bot_token}/sendPhoto"
        try:
            with BytesIO() as buffer:
                image.save(buffer, format="PNG")
                buffer.seek(0)
                files = {"photo": ("screenshot.png", buffer, "image/png")}
                data = {"chat_id": self._chat_id}
                if caption is not None:
                    data["caption"] = caption
                response = requests.post(url, data=data, files=files, timeout=10)
                response.raise_for_status()
                result = response.json()
                return isinstance(result, dict) and result.get("ok") is True
        except (requests.RequestException, OSError, ValueError):
            return False
