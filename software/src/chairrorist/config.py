"""Configuration management for ChairRorist."""
import copy
import json
import os
from typing import Any, Dict, Optional

from . import logging_setup, paths

logger = logging_setup.get_logger()


class Config:
    """Loads, merges and persists JSON configuration.

    User values are deep-merged over :attr:`DEFAULT_CONFIG` so that a partial
    ``config.json`` only overrides the keys it specifies.
    """

    DEFAULT_CONFIG: Dict[str, Any] = {
        "serial": {
            "baudrate": 9600,
            "timeout": 1,
        },
        "intervals": {
            "polling": 5,  # seconds
            "alert": 3600,  # seconds (1 hour)
        },
        "hotkeys": {
            "reset_timer": "ctrl+shift+alt+d",
        },
    }

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = (
            os.path.abspath(config_file) if config_file else paths.config_file_path()
        )
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        # deepcopy: a shallow copy would share nested dicts with DEFAULT_CONFIG
        # and let a user config silently mutate the class-level defaults.
        config = copy.deepcopy(self.DEFAULT_CONFIG)

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as handle:
                    user_config = json.load(handle)
                self._deep_update(config, user_config)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load config file %s: %s", self.config_file, exc)
                logger.warning("Using default configuration.")

        return config

    @staticmethod
    def _deep_update(base: Dict[str, Any], update: Dict[str, Any]) -> None:
        for key, value in update.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                Config._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Return a value addressed with dot notation (``serial.baudrate``)."""
        node: Any = self._config
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key: str, value: Any) -> None:
        """Set a value addressed with dot notation."""
        parts = key.split(".")
        node = self._config
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def save(self) -> None:
        """Persist the current configuration to disk."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as handle:
            json.dump(self._config, handle, indent=2)


def load_config(config_file: Optional[str] = None) -> Config:
    """Create a :class:`Config` using *config_file* or the default location."""
    return Config(config_file)
