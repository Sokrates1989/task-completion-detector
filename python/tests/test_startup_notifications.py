"""Check monitoring confirmations and transport results without sending messages."""

import contextlib
import io
import os
import smtplib
import unittest
from unittest.mock import Mock, patch

import requests
from PIL import Image

from task_completion_detector.models import Region
from task_completion_detector.monitor import MonitorSettings, RegionMonitor
from task_completion_detector.notifications.email_notifier import EmailNotifier
from task_completion_detector.notifications.telegram_notifier import TelegramNotifier
from task_completion_detector.screen_capture import ScreenCaptureError


class StartupNotificationTests(unittest.TestCase):
    """Run both real monitor loops against fake images and notification channels."""

    def setUp(self) -> None:
        self.config = Mock()
        self.config.load.return_value = {"notifications": {
            "useTelegram": True,
            "useEmail": True,
            "useLocalNotifications": True,
        }}
        self.events = []
        self.channels = {}
        for name in ("TelegramNotifier", "EmailNotifier", "MacOSNotifier"):
            patcher = patch("task_completion_detector.monitor." + name)
            factory = patcher.start()
            self.addCleanup(patcher.stop)
            self.channels[name] = factory.return_value
        self.telegram = self.channels["TelegramNotifier"]
        self.email = self.channels["EmailNotifier"]
        self.local = self.channels["MacOSNotifier"]
        self.telegram.is_configured.return_value = True
        self.email.is_configured.return_value = True
        self.telegram.send_message.side_effect = self._send_telegram
        self.telegram.send_photo.side_effect = self._send_telegram_photo
        self.email.send_simple_mail.side_effect = self._send_email
        for patcher in (
            patch("task_completion_detector.monitor.platform.system", return_value="Darwin"),
            patch("task_completion_detector.monitor.time.sleep"),
            patch.dict(os.environ, {"LANGUAGE": "en"}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.black = Image.new("RGB", (20, 10), "black")
        self.white = Image.new("RGB", (20, 10), "white")
        self.addCleanup(self.black.close)
        self.addCleanup(self.white.close)
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        for redirect in (
            contextlib.redirect_stdout(self.stdout),
            contextlib.redirect_stderr(self.stderr),
        ):
            redirect.__enter__()
            self.addCleanup(redirect.__exit__, None, None, None)

    def _send_telegram(self, _message: str) -> bool:
        self.events.append("telegram")
        return True

    def _send_telegram_photo(self, _image: Image.Image, caption: str) -> bool:
        self.events.append("telegram")
        return True

    def _send_email(self, _subject: str, _body: str) -> bool:
        self.events.append("email")
        return True

    def _monitor(self) -> RegionMonitor:
        """Use effective settings distinct from application defaults."""
        return RegionMonitor(
            "assistant panel", Region(601, 608, 20, 10),
            MonitorSettings(0.5, 1.0, 7.5), self.config,
        )

    def _run(self, is_change: bool) -> RegionMonitor:
        """Exercise counter resets before either mode reaches its final alert."""
        monitor = self._monitor()
        frames = iter(
            [self.black, self.white, self.black, self.white, self.white]
            if is_change else
            [self.black, self.black, self.white, self.white, self.white]
        )

        def capture() -> Image.Image:
            self.events.append("capture")
            return next(frames)

        with patch.object(monitor, "_capture_region", side_effect=capture) as grab:
            if is_change:
                monitor.monitor_until_change()
            else:
                monitor.monitor_until_stable()
        self.assertEqual(grab.call_count, 5)
        return monitor

    def test_stability_startup_describes_effective_criteria_then_completion_follows(self) -> None:
        self._run(is_change=False)
        self.assertEqual(self.events[:3], ["capture", "telegram", "email"])
        self.telegram.send_photo.assert_called_once()
        self.assertIs(self.telegram.send_photo.call_args.args[0], self.black)
        message = self.telegram.send_photo.call_args.kwargs["caption"]
        for expected in ("Monitoring started", "notify you", "no activity", "1 second"):
            self.assertIn(expected, message)
        for removed in ("x=", "y=", "20×10", " px", "0–255", "7.5", "checks", "task-watch", "assistant panel"):
            self.assertNotIn(removed, message)
        self.assertEqual(self.email.send_simple_mail.call_args_list[0].args, ("Monitoring started", message))
        self.telegram.send_message.assert_called_once()
        self.assertIn("No activity", self.telegram.send_message.call_args.args[0])
        self.local.send_notification.assert_called_once()

    def test_change_startup_matches_reference_image_and_confirmation_rule(self) -> None:
        self._run(is_change=True)
        self.assertEqual(self.events[:3], ["capture", "telegram", "email"])
        self.telegram.send_photo.assert_called_once()
        self.assertIs(self.telegram.send_photo.call_args.args[0], self.black)
        message = self.telegram.send_photo.call_args.kwargs["caption"]
        for expected in ("Monitoring started", "notify you", "watched area changes"):
            self.assertIn(expected, message)
        for removed in ("stability", "0–255", "7.5", "checks", "change-watch", "assistant panel"):
            self.assertNotIn(removed, message)
        self.telegram.send_message.assert_called_once()
        self.assertIn("watched area has changed", self.telegram.send_message.call_args.args[0])
        self.local.send_notification.assert_called_once()

    def test_initial_capture_failure_sends_no_notification_in_either_mode(self) -> None:
        monitor = self._monitor()
        with patch.object(monitor, "_capture_region", side_effect=ScreenCaptureError("capture.offscreen")):
            for method in (monitor.monitor_until_stable, monitor.monitor_until_change):
                with self.assertRaises(ScreenCaptureError):
                    method()
        self.telegram.send_message.assert_not_called()
        self.telegram.send_photo.assert_not_called()
        self.email.send_simple_mail.assert_not_called()
        self.local.send_notification.assert_not_called()

    def test_startup_preview_and_completion_screenshot_remain_separate(self) -> None:
        self.config.load.return_value["notifications"]["includeScreenshotInTelegram"] = True
        self._run(is_change=False)
        self.telegram.send_message.assert_not_called()
        self.assertEqual(self.telegram.send_photo.call_count, 2)
        startup, completion = self.telegram.send_photo.call_args_list
        self.assertIs(startup.args[0], self.black)
        self.assertIn("Monitoring started", startup.kwargs["caption"])
        self.assertIs(completion.args[0], self.white)
        self.assertIn("No activity", completion.kwargs["caption"])
        self.assertEqual(self.email.send_simple_mail.call_count, 2)

    def test_failed_channel_is_reported_and_other_channel_and_monitor_continue(self) -> None:
        self.telegram.send_photo.side_effect = None
        self.telegram.send_photo.return_value = False
        self._run(is_change=False)
        self.assertIn("Could not send the startup message via Telegram", self.stderr.getvalue())
        self.assertEqual(self.email.send_simple_mail.call_count, 2)
        self.local.send_notification.assert_called_once()

    def test_missing_credentials_do_not_send_and_report_both_enabled_channels(self) -> None:
        self.telegram.is_configured.return_value = False
        self.email.is_configured.return_value = False
        self._run(is_change=True)
        self.telegram.send_message.assert_not_called()
        self.telegram.send_photo.assert_not_called()
        self.email.send_simple_mail.assert_not_called()
        self.assertIn("Telegram", self.stderr.getvalue())
        self.assertIn("startup email", self.stderr.getvalue())
        self.local.send_notification.assert_called_once()

    def test_disabled_remote_channels_are_not_used(self) -> None:
        self.config.load.return_value["notifications"].update(useTelegram=False, useEmail=False)
        self._run(is_change=False)
        self.telegram.send_message.assert_not_called()
        self.telegram.send_photo.assert_not_called()
        self.email.send_simple_mail.assert_not_called()
        self.local.send_notification.assert_called_once()
        self.assertEqual(self.stderr.getvalue(), "")

    def test_startup_uses_german_locale(self) -> None:
        with patch.dict(os.environ, {"LANGUAGE": "de"}):
            self._run(is_change=True)
        message = self.telegram.send_photo.call_args.kwargs["caption"]
        self.assertIn("Überwachung gestartet", message)
        self.assertIn("wenn sich der beobachtete Bereich verändert", message)
        for removed in ("x=", "y=", "20×10", " px", "0–255", "Bildabweichung", "Prüfungen", "change-watch"):
            self.assertNotIn(removed, message)
        self.assertEqual(self.email.send_simple_mail.call_args_list[0].args[0], "Überwachung gestartet")
        self.assertIn("hat sich verändert", self.telegram.send_message.call_args.args[0])
        self.assertEqual(self.email.send_simple_mail.call_args.args[0], "Beobachteter Bereich verändert")


class TelegramResultTests(unittest.TestCase):
    """Distinguish Telegram API acceptance from rejected or failed sends."""

    def setUp(self) -> None:
        config = Mock()
        config.load.return_value = {"telegram": {"botToken": "example-token", "chatID": "example-chat"}}
        self.notifier = TelegramNotifier(config)
        self.image = Image.new("RGB", (20, 10), "red")
        self.addCleanup(self.image.close)

    def test_success_requires_positive_api_result(self) -> None:
        with patch("task_completion_detector.notifications.telegram_notifier.requests.post") as post:
            for response, expected in (({"ok": True}, True), ({"ok": False}, False), ({}, False), (None, False)):
                with self.subTest(response=response):
                    post.return_value.json.return_value = response
                    self.assertIs(self.notifier.send_message("startup"), expected)
            self.assertEqual(post.call_args.kwargs["timeout"], 10)

    def test_http_network_and_malformed_response_failures_return_false(self) -> None:
        with patch("task_completion_detector.notifications.telegram_notifier.requests.post") as post:
            post.side_effect = requests.Timeout("example timeout")
            self.assertFalse(self.notifier.send_message("startup"))
            post.side_effect = None
            post.return_value.raise_for_status.side_effect = requests.HTTPError("example rejection")
            self.assertFalse(self.notifier.send_message("startup"))
            post.return_value.raise_for_status.side_effect = None
            post.return_value.json.side_effect = ValueError("not JSON")
            self.assertFalse(self.notifier.send_message("startup"))

    def test_missing_credentials_do_not_contact_telegram(self) -> None:
        self.notifier._bot_token = ""
        with patch("task_completion_detector.notifications.telegram_notifier.requests.post") as post:
            self.assertFalse(self.notifier.send_message("startup"))
        post.assert_not_called()

    def test_photo_upload_contains_exact_region_png_and_caption_and_closes_buffer(self) -> None:
        uploaded = {}
        response = Mock()
        response.json.return_value = {"ok": True}

        def post(_url: str, **kwargs) -> Mock:
            uploaded.update(kwargs)
            buffer = kwargs["files"]["photo"][1]
            with Image.open(io.BytesIO(buffer.read())) as decoded:
                self.assertEqual(decoded.size, self.image.size)
                self.assertEqual(decoded.tobytes(), self.image.tobytes())
            return response

        with patch("task_completion_detector.notifications.telegram_notifier.requests.post", side_effect=post):
            self.assertTrue(self.notifier.send_photo(self.image, caption="Monitoring started"))
        self.assertEqual(uploaded["data"]["caption"], "Monitoring started")
        self.assertEqual(uploaded["timeout"], 10)
        self.assertTrue(uploaded["files"]["photo"][1].closed)
        self.assertEqual(self.image.getpixel((0, 0)), (255, 0, 0))

    def test_photo_http_api_network_and_json_failures_return_false(self) -> None:
        with patch("task_completion_detector.notifications.telegram_notifier.requests.post") as post:
            post.return_value.json.return_value = {"ok": False}
            self.assertFalse(self.notifier.send_photo(self.image))
            post.return_value.raise_for_status.side_effect = requests.HTTPError("example rejection")
            self.assertFalse(self.notifier.send_photo(self.image))
            post.return_value.raise_for_status.side_effect = None
            post.return_value.json.side_effect = ValueError("not JSON")
            self.assertFalse(self.notifier.send_photo(self.image))
            post.side_effect = requests.Timeout("example timeout")
            self.assertFalse(self.notifier.send_photo(self.image))

    def test_missing_photo_or_credentials_does_not_contact_telegram(self) -> None:
        with patch("task_completion_detector.notifications.telegram_notifier.requests.post") as post:
            self.assertFalse(self.notifier.send_photo(None))
            self.notifier._bot_token = ""
            self.assertFalse(self.notifier.send_photo(self.image))
        post.assert_not_called()

    def test_photo_encoding_failure_closes_buffer_without_http_request(self) -> None:
        buffer = io.BytesIO()
        with patch("task_completion_detector.notifications.telegram_notifier.BytesIO", return_value=buffer):
            with patch.object(self.image, "save", side_effect=OSError("encoding failed")):
                with patch("task_completion_detector.notifications.telegram_notifier.requests.post") as post:
                    self.assertFalse(self.notifier.send_photo(self.image))
        self.assertTrue(buffer.closed)
        post.assert_not_called()


class EmailResultTests(unittest.TestCase):
    """Keep SMTP results observable without connecting to a mail server."""

    def setUp(self) -> None:
        config = Mock()
        config.load.return_value = {"email": {
            "smtp_server": "smtp.example.invalid", "smtp_port": "465",
            "mail": "sender@example.invalid", "password": "example-password",
            "receiver": "recipient@example.invalid",
        }}
        self.notifier = EmailNotifier(config)

    def test_accepted_email_returns_true_and_has_bounded_socket_wait(self) -> None:
        with patch("task_completion_detector.notifications.email_notifier.smtplib.SMTP_SSL") as smtp:
            server = smtp.return_value.__enter__.return_value
            server.send_message.return_value = {}
            self.assertTrue(self.notifier.send_simple_mail("Überwachung gestartet", "Bereich prüfen"))
            self.assertEqual(smtp.call_args.kwargs["timeout"], 10)
            self.assertIs(smtp.call_args.kwargs["context"], self.notifier._ssl_context)
            email = server.send_message.call_args.args[0]
            self.assertEqual(email["Subject"], "Überwachung gestartet")
            self.assertEqual(email.get_payload()[0].get_payload(decode=True).decode("utf-8"), "Bereich prüfen")

    def test_smtp_rejection_and_connection_errors_return_false(self) -> None:
        with patch("task_completion_detector.notifications.email_notifier.smtplib.SMTP_SSL") as smtp:
            server = smtp.return_value.__enter__.return_value
            server.send_message.return_value = {"recipient@example.invalid": (550, b"rejected")}
            self.assertFalse(self.notifier.send_simple_mail("startup", "body"))
            server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"rejected")
            self.assertFalse(self.notifier.send_simple_mail("startup", "body"))
            smtp.side_effect = OSError("example connection failure")
            self.assertFalse(self.notifier.send_simple_mail("startup", "body"))

    def test_missing_credentials_do_not_connect_to_smtp(self) -> None:
        self.notifier._password = ""
        with patch("task_completion_detector.notifications.email_notifier.smtplib.SMTP_SSL") as smtp:
            self.assertFalse(self.notifier.send_simple_mail("startup", "body"))
        smtp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
