import json
import os
from typing import Any, Dict, Optional


class ConfigLoader:
    """Load and provide access to config/config.txt (JSON).

    You are expected to create config/config.txt from config.txt.template
    and fill in your secrets locally.
    """

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self._base_dir = base_dir
        self._config_path = os.path.join(self._base_dir, "config", "config.txt")
        self._config: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        if self._config is None:
            if not os.path.exists(self._config_path):
                raise FileNotFoundError(
                    f"Config file not found: {self._config_path}. "
                    "Copy config/config.txt.template to config/config.txt and fill it in."
                )
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        return self._config

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        cfg = self.load()
        return cfg.get(key, default)

    def get_region(self, name: str) -> Dict[str, Any]:
        cfg = self.load()
        regions = cfg.get("regions", {})
        if name not in regions:
            raise KeyError(f"Region '{name}' not found in config. Configure it via select-region first.")
        return regions[name]

    def save_region(self, name: str, region: Dict[str, Any]) -> None:
        cfg = self.load()
        regions = cfg.setdefault("regions", {})
        regions[name] = region
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
