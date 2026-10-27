"""Verify stale-region recovery without capturing the real desktop."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image, UnidentifiedImageError

from task_completion_detector.models import Region
from task_completion_detector.screen_capture import (
    ScreenCaptureError,
    _macos_display_bounds,
    capture_region,
)


class ScreenCaptureTests(unittest.TestCase):
    """Check display geometry and failure translation at the capture boundary."""

    def setUp(self) -> None:
        self.image = Image.new("RGB", (53, 13))
        self.addCleanup(self.image.close)
        for target, value in (
            ("platform.system", "Darwin"),
            ("_macos_display_bounds", [(0, 0, 1920, 1080)]),
            ("ImageGrab.grab", self.image),
        ):
            patcher = patch(
                "task_completion_detector.screen_capture." + target,
                return_value=value,
            )
            self.addCleanup(patcher.stop)
            mock = patcher.start()
            if target == "ImageGrab.grab":
                self.grab = mock
            elif target == "_macos_display_bounds":
                self.displays = mock

    def test_disconnected_left_display_is_rejected_before_capture(self) -> None:
        with self.assertRaisesRegex(ScreenCaptureError, "capture.offscreen"):
            capture_region(Region(-719, 70, 53, 13))
        self.grab.assert_not_called()

    def test_negative_coordinates_on_connected_displays_are_valid(self) -> None:
        self.displays.return_value = [(-1920, -1080, 0, 1080), (0, 0, 1920, 1080)]
        for region in (Region(-719, 70, 53, 13), Region(-719, -100, 53, 13)):
            with self.subTest(region=region):
                self.assertIs(capture_region(region), self.image)
                self.grab.assert_called_with(
                    bbox=(region.x, region.y, region.x + 53, region.y + 13)
                )

    def test_edges_and_gaps_do_not_count_as_visible(self) -> None:
        self.displays.return_value = [(0, 0, 100, 100), (200, 0, 300, 100)]
        for region in (
            Region(-10, 0, 10, 10),
            Region(300, 0, 10, 10),
            Region(0, -10, 10, 10),
            Region(0, 100, 10, 10),
            Region(150, 0, 10, 10),
        ):
            with self.subTest(region=region):
                with self.assertRaisesRegex(ScreenCaptureError, "capture.offscreen"):
                    capture_region(region)
        self.grab.assert_not_called()

    def test_partially_visible_region_keeps_existing_capture_behavior(self) -> None:
        self.assertIs(capture_region(Region(-10, 0, 20, 10)), self.image)
        self.grab.assert_called_once_with(bbox=(-10, 0, 10, 10))

    def test_nonpositive_dimensions_are_rejected_before_capture(self) -> None:
        for width, height in ((0, 10), (10, 0), (-1, 10), (10, -1)):
            with self.subTest(width=width, height=height):
                with self.assertRaisesRegex(ScreenCaptureError, "capture.invalid_size"):
                    capture_region(Region(0, 0, width, height))
        self.grab.assert_not_called()

    def test_unavailable_display_query_defers_to_pillow(self) -> None:
        self.displays.return_value = None
        self.assertIs(capture_region(Region(-719, 70, 53, 13)), self.image)

    def test_other_platforms_keep_existing_pillow_capture(self) -> None:
        with patch("task_completion_detector.screen_capture.platform.system", return_value="Windows"):
            self.assertIs(capture_region(Region(0, 0, 53, 13)), self.image)
        self.displays.assert_not_called()

    def test_capture_failures_keep_their_original_cause(self) -> None:
        for failure in (UnidentifiedImageError("empty screenshot"), OSError("capture denied")):
            with self.subTest(failure=failure):
                self.grab.side_effect = failure
                with self.assertRaisesRegex(ScreenCaptureError, "capture.failed") as error:
                    capture_region(Region(0, 0, 53, 13))
                self.assertIs(error.exception.__cause__, failure)


class DisplayQueryTests(unittest.TestCase):
    """Exercise the optional macOS dependency without querying real displays."""

    def test_quartz_bounds_use_global_coordinates(self) -> None:
        quartz = SimpleNamespace(
            CGGetActiveDisplayList=lambda *_: (0, [1], 1),
            CGDisplayBounds=lambda _: SimpleNamespace(
                origin=SimpleNamespace(x=-1920, y=-100),
                size=SimpleNamespace(width=1920, height=1080),
            ),
        )
        with patch.dict("sys.modules", {"Quartz": quartz}):
            self.assertEqual(_macos_display_bounds(), [(-1920, -100, 0, 980)])

    def test_failed_or_empty_queries_defer_to_pillow(self) -> None:
        for result in ((1, None, 0), (0, [], 0)):
            with self.subTest(result=result):
                quartz = SimpleNamespace(CGGetActiveDisplayList=lambda *_: result)
                with patch.dict("sys.modules", {"Quartz": quartz}):
                    self.assertIsNone(_macos_display_bounds())

    def test_missing_quartz_defers_to_pillow(self) -> None:
        with patch.dict("sys.modules", {"Quartz": None}):
            self.assertIsNone(_macos_display_bounds())


if __name__ == "__main__":
    unittest.main()
