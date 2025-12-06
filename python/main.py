import argparse
import sys
from typing import Any, Dict

from task_completion_detector.config_loader import ConfigLoader
from task_completion_detector.monitor import MonitorSettings, RegionMonitor


def _load_monitor_settings(cfg: Dict[str, Any]) -> MonitorSettings:
    monitor_cfg = cfg.get("monitor", {})
    interval = float(monitor_cfg.get("intervalSeconds", 1.0))
    stable_seconds = float(monitor_cfg.get("stableSecondsThreshold", 30.0))
    diff_threshold = float(monitor_cfg.get("differenceThreshold", 2.0))
    return MonitorSettings(interval_seconds=interval, stable_seconds_threshold=stable_seconds, difference_threshold=diff_threshold)


def cmd_select_region(args: argparse.Namespace) -> None:
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


def cmd_monitor(args: argparse.Namespace) -> None:
    config_loader = ConfigLoader()
    cfg = config_loader.load()
    region_cfg = config_loader.get_region(args.name)

    # Import Region lazily to avoid issues if typing-only imports change
    from task_completion_detector.region_selector import Region

    region = Region(
        x=int(region_cfg["x"]),
        y=int(region_cfg["y"]),
        width=int(region_cfg["width"]),
        height=int(region_cfg["height"]),
    )

    settings = _load_monitor_settings(cfg)

    monitor = RegionMonitor(args.name, region, settings, config_loader)
    monitor.monitor_until_stable()


def cmd_setup_config(_args: argparse.Namespace) -> None:
    from task_completion_detector.config_setup import run_interactive

    run_interactive()


def main() -> None:
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
    p_monitor.set_defaults(func=cmd_monitor)

    p_setup = subparsers.add_parser("setup-config", help="Guided setup for configuration file")
    p_setup.set_defaults(func=cmd_setup_config)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
