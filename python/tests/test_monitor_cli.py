"""Verify actionable capture errors through both real CLI monitoring paths."""

import contextlib
import io
import os
import unittest
from unittest.mock import Mock, patch

from PIL import UnidentifiedImageError

import main


class MonitorCliTests(unittest.TestCase):
    """Keep display failures local and disable every notification transport."""

    def setUp(self) -> None:
        config = Mock()
        config.load.return_value = {
            "notifications": {
                "useTelegram": False,
                "useEmail": False,
                "useLocalNotifications": False,
            },
        }
        config.get_region.return_value = {"x": -719, "y": 70, "width": 53, "height": 13}
        patchers = (
            patch("main.ConfigLoader", return_value=config),
            patch("task_completion_detector.screen_capture.platform.system", return_value="Darwin"),
            patch("task_completion_detector.screen_capture._macos_display_bounds", return_value=[(0, 0, 1920, 1080)]),
            patch.dict(os.environ, {"LANGUAGE": "en"}),
        )
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def _run_cli(self, mode: list, name: str = "default") -> str:
        """Return stderr after a monitoring failure exits with status one."""
        output = io.StringIO()
        with patch("sys.argv", ["main.py", "monitor", "--name", name] + mode):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(output):
                with self.assertRaises(SystemExit) as error:
                    main.main()
        self.assertEqual(error.exception.code, 1)
        self.assertNotIn("Traceback", output.getvalue())
        return output.getvalue()

    def test_offscreen_region_has_recovery_command_in_both_modes(self) -> None:
        with patch("task_completion_detector.screen_capture.ImageGrab.grab") as grab:
            for mode in ([], ["--change"]):
                with self.subTest(mode=mode):
                    output = self._run_cli(mode)
                    self.assertIn("outside the connected displays", output)
                    launcher = "change-watch" if mode else "task-watch"
                    self.assertIn(launcher + " --select-region default", output)
                    self.assertIn("x=-719", output)
            grab.assert_not_called()

    def test_capture_failure_has_permission_guidance_in_both_modes(self) -> None:
        with patch("task_completion_detector.screen_capture._macos_display_bounds", return_value=None):
            with patch("task_completion_detector.screen_capture.ImageGrab.grab", side_effect=UnidentifiedImageError("empty PNG")):
                for mode in ([], ["--change"]):
                    with self.subTest(mode=mode):
                        output = self._run_cli(mode)
                        self.assertIn("Could not capture region", output)
                        self.assertIn("Screen Recording", output)
                        self.assertNotIn("empty PNG", output)

    def test_named_region_is_quoted_in_recovery_command(self) -> None:
        self.assertIn("task-watch --select-region 'assistant panel'", self._run_cli([], "assistant panel"))

    def test_windows_recovery_uses_supported_selection_flag(self) -> None:
        with patch("task_completion_detector.screen_capture.platform.system", return_value="Windows"):
            with patch("task_completion_detector.screen_capture.ImageGrab.grab", side_effect=OSError("capture denied")):
                output = self._run_cli(["--change"])
        self.assertIn("change-watch -r default", output)
        self.assertNotIn("Screen Recording", output)


if __name__ == "__main__":
    unittest.main()
