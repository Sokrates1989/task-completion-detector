import time
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from PIL import ImageChops, ImageGrab, ImageStat

from .config_loader import ConfigLoader
from .notifications import EmailNotifier, MacOSNotifier, TelegramNotifier

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
        self._use_macos = bool(notify_cfg.get("useMacOS", True))

        self._telegram = TelegramNotifier(self._config_loader) if self._use_telegram else None
        self._email = EmailNotifier(self._config_loader) if self._use_email else None
        self._macos = MacOSNotifier() if self._use_macos else None

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

    def _send_notifications(self, stable_seconds: float) -> None:
        message = f"No more activity detected in the selected area for {stable_seconds:.0f} seconds."
        if self._telegram and self._telegram.is_configured():
            self._telegram.send_message(message)
        if self._email and self._email.is_configured():
            self._email.send_simple_mail("Task completion detected", message)
        if self._macos:
            self._macos.send_notification(message)

    def monitor_until_stable(self) -> None:
        interval = self._settings.interval_seconds
        threshold_seconds = self._settings.stable_seconds_threshold
        diff_threshold = self._settings.difference_threshold

        stable_time = 0.0
        last_image = None

        print(
            f"Monitoring region '{self._name}' at interval {interval}s, "
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
                        f"Region '{self._name}' stable for {stable_time:.0f}s (score <= {diff_threshold}). Sending notifications."
                    )
                    self._send_notifications(stable_time)

                    if self._use_macos:
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
                    break

            last_image = current
            time.sleep(interval)
