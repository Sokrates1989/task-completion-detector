import subprocess
from typing import Optional


class MacOSNotifier:
    """Send native macOS notifications via AppleScript.

    Requires the `osascript` binary (available by default on macOS).
    """

    def __init__(self, title: str = "Task Completion Detector") -> None:
        self._title = title

    def send_notification(self, body: str, subtitle: Optional[str] = None) -> None:
        title_esc = self._title.replace("\"", "\\\"")
        body_esc = body.replace("\"", "\\\"")
        if subtitle:
            subtitle_esc = subtitle.replace("\"", "\\\"")
            script = f'display notification "{body_esc}" with title "{title_esc}" subtitle "{subtitle_esc}"'
        else:
            script = f'display notification "{body_esc}" with title "{title_esc}"'
        try:
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception:
            # Best-effort only; ignore failures.
            pass
