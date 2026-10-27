"""Capture saved regions, validating macOS display coordinates before Pillow runs.

Quartz is supplied by pynput on macOS. If it is unavailable or cannot report
displays, Pillow remains the capture authority. No screenshots are persisted here.
"""

import platform
from typing import List, Optional, Tuple

from PIL import Image, ImageGrab

from .models import Region

Bounds = Tuple[float, float, float, float]


class ScreenCaptureError(RuntimeError):
    """Carry a translation key for capture failures presented by the CLI."""


def _macos_display_bounds() -> Optional[List[Bounds]]:
    """Return active display rectangles, or None when Quartz cannot query them."""
    try:
        import Quartz
    except ImportError:
        return None

    error, displays, count = Quartz.CGGetActiveDisplayList(32, None, None)
    if error or not count:
        return None

    bounds = []
    for display in displays:
        rect = Quartz.CGDisplayBounds(display)
        bounds.append(
            (
                rect.origin.x,
                rect.origin.y,
                rect.origin.x + rect.size.width,
                rect.origin.y + rect.size.height,
            )
        )
    return bounds


def capture_region(region: Region) -> Image.Image:
    """Capture a region or raise ScreenCaptureError with an actionable error key.

    Negative coordinates are valid on displays left of or above the main display.
    Only regions with no overlap are rejected; partially visible regions retain
    Pillow's existing behavior. Capture OS errors keep their original cause.
    """
    if region.width <= 0 or region.height <= 0:
        raise ScreenCaptureError("capture.invalid_size")

    left, top = int(region.x), int(region.y)
    right, bottom = int(region.x + region.width), int(region.y + region.height)
    if platform.system() == "Darwin":
        displays = _macos_display_bounds()
        if displays is not None and not any(
            left < display_right
            and right > display_left
            and top < display_bottom
            and bottom > display_top
            for display_left, display_top, display_right, display_bottom in displays
        ):
            raise ScreenCaptureError("capture.offscreen")

    try:
        return ImageGrab.grab(bbox=(left, top, right, bottom))
    except OSError as error:
        raise ScreenCaptureError("capture.failed") from error
