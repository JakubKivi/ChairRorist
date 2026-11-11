"""Persistent user settings stored in the application-data directory.

Runtime choices such as the selected serial port are persisted here — next to
the accumulated statistics (``data.chairRorist``) — rather than in the
bundled ``config.json``, so they survive independently of the build.
"""
import json
import os
import tempfile

from . import paths

_SETTINGS_FILE = "settings.json"
_PORT_KEY = "port"


def settings_path() -> str:
    """Return the path of the persistent settings file."""
    return paths.app_data_path(_SETTINGS_FILE)


def load_settings() -> dict:
    """Return the persisted settings (empty dict when absent/invalid)."""
    try:
        with open(settings_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(settings: dict) -> None:
    """Atomically persist the settings dictionary."""
    path = settings_path()
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def get_port() -> str | None:
    """Return the user-selected serial port, if any."""
    port = load_settings().get(_PORT_KEY)
    return port if port else None


def set_port(port: str) -> None:
    """Persist the user-selected serial port."""
    settings = load_settings()
    settings[_PORT_KEY] = port
    save_settings(settings)
