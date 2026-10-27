"""Send configured email over verified SMTP SSL with bounded socket waits."""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from ..config_loader import ConfigLoader


class EmailNotifier:
    """Use the local SMTP credentials and configured notification recipient."""

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
        """Return whether all SMTP credentials and recipient fields are present."""
        return bool(self._smtp_server and self._smtp_port and self._sender_mail and self._password and self._receiver_mail)

    def send_simple_mail(self, subject: str, body: str) -> bool:
        """Return whether SMTP accepted the email for every requested recipient.

        Socket operations time out after ten seconds. Missing credentials,
        network failures and SMTP rejection return False without exposing
        credentials. SMTP acceptance does not guarantee inbox delivery.
        """
        if not self.is_configured():
            return False
        msg = MIMEMultipart()
        msg["From"] = self._sender_mail
        msg["To"] = self._receiver_mail
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP_SSL(
                self._smtp_server, self._smtp_port, context=self._ssl_context, timeout=10
            ) as server:
                server.login(self._sender_mail, self._password)
                return not server.send_message(msg)
        except OSError:
            return False
