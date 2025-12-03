import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from ..config_loader import ConfigLoader


class EmailNotifier:
    def __init__(self, config_loader: Optional[ConfigLoader] = None) -> None:
        self._config_loader = config_loader or ConfigLoader()
        cfg = self._config_loader.load()
        email_cfg = cfg.get("email", {})
        self._smtp_server: str = email_cfg.get("smtp_server", "")
        self._smtp_port: int = int(email_cfg.get("smtp_port", "0")) or 0
        self._sender_mail: str = email_cfg.get("mail", "")
        self._password: str = email_cfg.get("password", "")
        self._receiver_mail: str = email_cfg.get("receiver", "")
        self._ssl_context = ssl.create_default_context()

    def is_configured(self) -> bool:
        return bool(self._smtp_server and self._smtp_port and self._sender_mail and self._password and self._receiver_mail)

    def send_simple_mail(self, subject: str, body: str) -> None:
        if not self.is_configured():
            return
        msg = MIMEMultipart()
        msg["From"] = self._sender_mail
        msg["To"] = self._receiver_mail
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP_SSL(self._smtp_server, self._smtp_port, context=self._ssl_context) as server:
                server.login(self._sender_mail, self._password)
                server.send_message(msg)
        except Exception:
            # For now ignore, later we can log.
            pass
