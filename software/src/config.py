"""Configuration settings for ChairRorist application."""
import json
import os
from typing import Dict, Any


class Config:
    """Configuration manager for the application."""

    DEFAULT_CONFIG = {
        "serial": {
            "port": "COM3",
            "baudrate": 9600,
            "timeout": 1
        },
        "intervals": {
            "polling": 5,  # seconds
            "alert": 3600  # seconds (1 hour)
        },
        "hotkeys": {
            "reset_timer": "ctrl+shift+alt+d"
        }
    }

    def __init__(self, config_file: str = None):
        """Initialize configuration.

        Args:
            config_file: Path to configuration file. If None, uses default path.
        """
        if config_file is None:
            # Determine config file path
            if getattr(os.sys, "frozen", False):
                base_path = os.path.dirname(os.sys.executable)
                config_file = os.path.join(base_path, "..", "config.json")
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
                config_file = os.path.join(base_path, "..", "..", "config.json")

        self.config_file = os.path.abspath(config_file)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                self._deep_update(config, user_config)
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
                print("Using default configuration.")
        return self.DEFAULT_CONFIG.copy()

    def _deep_update(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Recursively update a dictionary."""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'serial.port')."""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value

    def save(self) -> None:
        """Save current configuration to file."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2)


# Global config instance
config = Config()