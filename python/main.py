"""Dispatch region selection, monitoring, and configuration commands."""

import argparse
import platform
import shlex
import sys
from typing import Any, Dict

from task_completion_detector.config_loader import ConfigLoader
from task_completion_detector.i18n import translate
from task_completion_detector.models import Region
from task_completion_detector.monitor import MonitorSettings, RegionMonitor
from task_completion_detector.screen_capture import ScreenCaptureError


def _load_monitor_settings(cfg: Dict[str, Any], mode: str = "stable") -> MonitorSettings:
    """Load monitor settings, supporting separate configs for stable vs change modes.

    - For stability mode (task-watch), values are read from the legacy "monitor" section.
    - For change mode (change-watch), values are read from "monitorChange" when present,
      falling back to "monitor" for backward compatibility.
    """

    if mode == "change":
        monitor_cfg = cfg.get("monitorChange") or cfg.get("monitor", {})
    else:
        monitor_cfg = cfg.get("monitor", {})

    interval = float(monitor_cfg.get("intervalSeconds", 1.0))
    stable_seconds = float(monitor_cfg.get("stableSecondsThreshold", 30.0))
    diff_threshold = float(monitor_cfg.get("differenceThreshold", 10.0))

    return MonitorSettings(
        interval_seconds=interval,
        stable_seconds_threshold=stable_seconds,
        difference_threshold=diff_threshold,
    )


def cmd_select_region(args: argparse.Namespace) -> None:
    """Interactively capture and save a screen region.

    Args:
        args (argparse.Namespace): Parsed CLI args containing the region name and optional aliases.
    """
    from task_completion_detector.region_selector import RegionSelector

    config_loader = ConfigLoader()
    selector = RegionSelector(config_loader)
    region = selector.select_region(args.name)
    if region is None:
        print("Region selection cancelled.")
        sys.exit(1)

    print(
        f"Saved region '{args.name}': x={region.x}, y={region.y}, "
        f"width={region.width}, height={region.height}"
    )
    # Optionally save the same region under additional names
    for extra_name in getattr(args, "also_name", []) or []:
        if extra_name == args.name:
            continue
        config_loader.save_region(
            extra_name,
            {
                "x": region.x,
                "y": region.y,
                "width": region.width,
                "height": region.height,
            },
        )
        print(
            f"Also saved region '{extra_name}': x={region.x}, y={region.y}, "
            f"width={region.width}, height={region.height}"
        )


def _report_capture_error(
    name: str, region: Region, error: ScreenCaptureError, is_change: bool
) -> None:
    """Write localized recovery instructions to stderr without a traceback."""
    launcher = "change-watch" if is_change else "task-watch"
    select_flag = "-r" if platform.system() == "Windows" else "--select-region"
    command = shlex.join([launcher, select_flag, name])
    print(
        translate(
            str(error),
            name=name,
            x=region.x,
            y=region.y,
            width=region.width,
            height=region.height,
            command=command,
        ),
        file=sys.stderr,
    )
    if str(error) == "capture.failed" and platform.system() == "Darwin":
        print(translate("capture.macos_permission"), file=sys.stderr)


def cmd_monitor(args: argparse.Namespace) -> None:
    """Monitor a region, falling back to interactive selection if the name is unknown.

    Args:
        args (argparse.Namespace): Parsed CLI args with region name, monitoring mode, and overrides.
    """
    config_loader = ConfigLoader()
    cfg = config_loader.load()
    region_cfg: Dict[str, Any]
    region_obj = None
    try:
        region_cfg = config_loader.get_region(args.name)
    except KeyError:
        print(f"Region '{args.name}' not found. Launching interactive selection...")
        from task_completion_detector.region_selector import RegionSelector

        selector = RegionSelector(config_loader)
        region_obj = selector.select_region(args.name)
        if region_obj is None:
            print("Region selection cancelled.")
            sys.exit(1)
        region_cfg = {
            "x": region_obj.x,
            "y": region_obj.y,
            "width": region_obj.width,
            "height": region_obj.height,
        }

    region = region_obj or Region(
        x=int(region_cfg["x"]),
        y=int(region_cfg["y"]),
        width=int(region_cfg["width"]),
        height=int(region_cfg["height"]),
    )

    # Choose monitoring settings based on --change flag
    is_change = getattr(args, "change", False)
    mode = "change" if is_change else "stable"
    settings = _load_monitor_settings(cfg, mode=mode)

    # Allow overriding stableSecondsThreshold on a per-run basis in stability mode
    stable_override = getattr(args, "stable_seconds", None)
    if (not is_change) and (stable_override is not None):
        settings.stable_seconds_threshold = float(stable_override)

    monitor = RegionMonitor(args.name, region, settings, config_loader)

    try:
        if is_change:
            monitor.monitor_until_change()
        else:
            monitor.monitor_until_stable()
    except ScreenCaptureError as error:
        _report_capture_error(args.name, region, error, is_change)
        raise SystemExit(1) from None


def cmd_setup_config(_args: argparse.Namespace) -> None:
    """Run the guided configuration setup."""
    from task_completion_detector.config_setup import run_interactive

    run_interactive()


def main() -> None:
    """Entry point for the Task Completion Detector CLI."""
    parser = argparse.ArgumentParser(description="Task Completion Detector CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_select = subparsers.add_parser("select-region", help="Select and save a screen region")
    p_select.add_argument("--name", required=True, help="Name of the region to save")
    p_select.add_argument(
        "--also-name",
        action="append",
        default=[],
        help="Additional region names to save the same region under",
    )
    p_select.set_defaults(func=cmd_select_region)

    p_monitor = subparsers.add_parser("monitor", help="Monitor a previously defined region")
    p_monitor.add_argument("--name", required=True, help="Name of the region to monitor")
    p_monitor.add_argument(
        "--change",
        action="store_true",
        help="Watch for changes instead of stability (notify immediately when region changes)",
    )
    p_monitor.add_argument(
        "--stable-seconds",
        type=float,
        default=None,
        help="Override stableSecondsThreshold for this run (stability mode only)",
    )
    p_monitor.set_defaults(func=cmd_monitor)

    p_setup = subparsers.add_parser("setup-config", help="Guided setup for configuration file")
    p_setup.set_defaults(func=cmd_setup_config)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
