import platform
import time
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from PIL import Image, ImageChops, ImageGrab, ImageStat

from .config_loader import ConfigLoader
from .notifications import EmailNotifier, MacOSNotifier, TelegramNotifier, WindowsNotifier

if TYPE_CHECKING:
    # Only used for typing; avoid importing Tk-dependent code at runtime
    from .region_selector import Region


@dataclass
class MonitorSettings:
    interval_seconds: float
    stable_seconds_threshold: float
    difference_threshold: float


class RegionMonitor:
    """Monitor a screen region and notify when it becomes visually stable."""

    def __init__(
        self,
        name: str,
        region: "Region",
        settings: MonitorSettings,
        config_loader: Optional[ConfigLoader] = None,
    ) -> None:
        self._name = name
        self._region = region
        self._settings = settings
        self._config_loader = config_loader or ConfigLoader()

        cfg = self._config_loader.load()
        notify_cfg = cfg.get("notifications", {})
        self._use_telegram = bool(notify_cfg.get("useTelegram", True))
        self._use_email = bool(notify_cfg.get("useEmail", False))
        self._use_local = bool(
            notify_cfg.get("useLocalNotifications", notify_cfg.get("useMacOS", True))
        )
        self._include_screenshot_telegram = bool(
            notify_cfg.get("includeScreenshotInTelegram", False)
        )

        self._telegram = TelegramNotifier(self._config_loader) if self._use_telegram else None
        self._email = EmailNotifier(self._config_loader) if self._use_email else None
        
        # Use platform-appropriate local notifier
        self._local_notifier = None
        if self._use_local:
            if platform.system() == "Darwin":
                self._local_notifier = MacOSNotifier()
            elif platform.system() == "Windows":
                self._local_notifier = WindowsNotifier()

    def _capture_region(self):
        bbox = (
            int(self._region.x),
            int(self._region.y),
            int(self._region.x + self._region.width),
            int(self._region.y + self._region.height),
        )
        return ImageGrab.grab(bbox=bbox)

    @staticmethod
    def _difference_score(img1, img2) -> float:
        # Compute mean absolute difference in grayscale.
        diff = ImageChops.difference(img1.convert("L"), img2.convert("L"))
        stat = ImageStat.Stat(diff)
        return float(stat.mean[0])  # 0..255

    def _send_notifications(
        self,
        message: str,
        subject: str = "Task completion detected",
        image=None,
        before_image=None,
        after_image=None,
    ) -> None:
        if self._telegram and self._telegram.is_configured():
            if getattr(self, "_include_screenshot_telegram", False):
                send_image = image
                caption = message

                if before_image is not None or after_image is not None:
                    if before_image is not None and after_image is not None:
                        try:
                            w = before_image.width + after_image.width
                            h = max(before_image.height, after_image.height)
                            combined = Image.new("RGB", (w, h))
                            combined.paste(before_image.convert("RGB"), (0, 0))
                            combined.paste(after_image.convert("RGB"), (before_image.width, 0))
                            send_image = combined
                            caption = f"{message}\n(Left: before, Right: after)"
                        except Exception:
                            send_image = after_image or before_image
                    else:
                        send_image = after_image or before_image

                if send_image is not None:
                    self._telegram.send_photo(send_image, caption=caption)
                else:
                    self._telegram.send_message(message)
            else:
                self._telegram.send_message(message)
        if self._email and self._email.is_configured():
            self._email.send_simple_mail(subject, message)
        if self._local_notifier:
            self._local_notifier.send_notification(message)

    def monitor_until_stable(self) -> None:
        interval = self._settings.interval_seconds
        threshold_seconds = self._settings.stable_seconds_threshold
        diff_threshold = self._settings.difference_threshold

        stable_time = 0.0
        last_image = None

        label = "default region" if self._name in ("default", "windsurf_panel") else f"region '{self._name}'"
        print(
            f"Monitoring {label} (x={self._region.x}, y={self._region.y}, "
            f"width={self._region.width}, height={self._region.height}) at interval {interval}s, "
            f"declaring stable after {threshold_seconds}s with diff threshold {diff_threshold}..."
        )

        while True:
            current = self._capture_region()

            if last_image is not None:
                score = self._difference_score(last_image, current)
                # Debug print; later we can gate behind a flag if too noisy.
                # print(f"diff score: {score}")

                if score <= diff_threshold:
                    stable_time += interval
                else:
                    stable_time = 0.0

                if stable_time >= threshold_seconds:
                    print(
                        f"Selected region stable for {stable_time:.0f}s (score <= {diff_threshold}). Sending notifications."
                    )
                    message = f"No more activity detected in the selected area for {stable_time:.0f} seconds."
                    self._send_notifications(message, image=current)

                    if self._use_local and platform.system() == "Darwin":
                        print(
                            "\nmacOS notification hint:"\
                            "\n- If you did not see the popup, open the Notification Center (top-right) and look for 'Task Completion Detector'."\
                            "\n- For more intrusive alerts, right-click that notification, choose 'Mitteilungs-Einstellungen…' and set for 'Skripteditor' / the notification app:"\
                            "\n  * Hinweisstil: 'Dauerhaft' (Alerts)"\
                            "\n  * Schreibtisch / Mitteilungszentrale / Sperrbildschirm: aktiviert"\
                            "\n  * Ton für Mitteilung wiedergeben: aktiviert"\
                            "\n  * Vorschauen zeigen: 'Immer'"\
                            "\n  * Mitteilungsgruppierung: 'Nach App'"
                        )
                    elif self._use_local and platform.system() == "Windows":
                        print(
                            "\nWindows notification hint:"\
                            "\n- If you did not see the popup, check the Action Center (Win+A) for 'Task Completion Detector'."\
                            "\n- For better notifications, install the BurntToast module: Install-Module -Name BurntToast -Scope CurrentUser"
                        )
                    break

            last_image = current
            time.sleep(interval)

    def monitor_until_change(self) -> None:
        """Monitor a region and notify immediately when a change is detected.

        This is the inverse of monitor_until_stable: instead of waiting for the
        region to become stable, we notify as soon as any change is detected.
        Useful for watching static indicators (e.g., a pause button) that change
        when a long-running task completes.
        """
        interval = self._settings.interval_seconds
        diff_threshold = self._settings.difference_threshold

        label = "default region" if self._name in ("default", "windsurf_panel") else f"region '{self._name}'"
        print(
            f"Watching {label} (x={self._region.x}, y={self._region.y}, "
            f"width={self._region.width}, height={self._region.height}) for changes at interval {interval}s, "
            f"notifying when diff > {diff_threshold}..."
        )

        # Capture initial reference image
        reference_image = self._capture_region()
        print("Reference image captured. Watching for changes...")

        while True:
            time.sleep(interval)
            current = self._capture_region()

            score = self._difference_score(reference_image, current)

            if score > diff_threshold:
                print(
                    f"Change detected! (diff score: {score:.2f} > {diff_threshold}). Sending notifications."
                )
                message = f"Change detected in the monitored area! The watched region has changed."
                self._send_notifications(
                    message,
                    subject="Change detected",
                    before_image=reference_image,
                    after_image=current,
                )

                if self._use_local and platform.system() == "Darwin":
                    print(
                        "\nmacOS notification hint:"\
                        "\n- If you did not see the popup, open the Notification Center (top-right) and look for 'Task Completion Detector'."
                    )
                elif self._use_local and platform.system() == "Windows":
                    print(
                        "\nWindows notification hint:"\
                        "\n- If you did not see the popup, check the Action Center (Win+A) for 'Task Completion Detector'."\
                        "\n- For better notifications, install the BurntToast module: Install-Module -Name BurntToast -Scope CurrentUser"
                    )
                break
