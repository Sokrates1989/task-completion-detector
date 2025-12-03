from dataclasses import dataclass
from typing import Optional, Tuple

from pynput.mouse import Controller

from .config_loader import ConfigLoader


@dataclass
class Region:
    x: int
    y: int
    width: int
    height: int


class RegionSelector:
    """Region selector using mouse clicks instead of manual pixel entry.

    Flow:
    - Ask user to move mouse to TOP-LEFT of region and press Enter
    - Capture mouse coordinates
    - Ask user to move mouse to BOTTOM-RIGHT and press Enter
    - Save resulting rectangle to config
    """

    def __init__(self, config_loader: Optional[ConfigLoader] = None) -> None:
        self._config_loader = config_loader or ConfigLoader()
        self._mouse = Controller()

    def _capture_point(self, label: str) -> Tuple[int, int]:
        input(f"Move mouse to {label} corner, then press Enter here...")
        x, y = self._mouse.position
        x_i, y_i = int(x), int(y)
        print(f"Captured {label} at x={x_i}, y={y_i}")
        return x_i, y_i

    def select_region(self, name: str) -> Optional[Region]:
        print("=== AI Watch Region Selection (mouse-based) ===")
        print("This will record two mouse positions:")
        print("  1) TOP-LEFT of the region")
        print("  2) BOTTOM-RIGHT of the region")

        x1, y1 = self._capture_point("TOP-LEFT")
        x2, y2 = self._capture_point("BOTTOM-RIGHT")

        if x1 == x2 or y1 == y2:
            print("Points are identical; region selection cancelled.")
            return None

        x_min = min(x1, x2)
        y_min = min(y1, y2)
        x_max = max(x1, x2)
        y_max = max(y1, y2)

        region = Region(x=x_min, y=y_min, width=x_max - x_min, height=y_max - y_min)

        self._config_loader.save_region(
            name,
            {"x": region.x, "y": region.y, "width": region.width, "height": region.height},
        )

        print(
            f"Saved region '{name}': x={region.x}, y={region.y}, "
            f"width={region.width}, height={region.height}"
        )
        return region
