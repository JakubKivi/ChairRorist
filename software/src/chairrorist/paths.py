"""Filesystem path resolution for ChairRorist.

This module is the single place that knows how to locate files, both when
running from source and when running as a PyInstaller bundle.  It also keeps
user-writable data out of the read-only ``_MEIPASS`` directory that
PyInstaller creates at runtime.
"""
import os
import sys

APP_NAME = "ChairRorist"


def is_frozen() -> bool:
    """Return ``True`` when running inside a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def _bundle_base() -> str:
    """Return the directory that contains bundled, read-only assets."""
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))

    # Running from source: software/src/chairrorist/ -> repository root.
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
    )


def resource_path(*parts: str) -> str:
    """Return an absolute path to a bundled, read-only resource."""
    return os.path.abspath(os.path.join(_bundle_base(), *parts))


def app_data_path(*parts: str) -> str:
    """Return an absolute path to a user-writable data location."""
    if is_frozen():
        base = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME
        )
    else:
        # Keep development data inside the repository's data/ directory.
        base = resource_path("data")
    return os.path.abspath(os.path.join(base, *parts))


def config_file_path() -> str:
    """Return the location of the user-editable ``config.json``."""
    if is_frozen():
        return os.path.abspath(
            os.path.join(os.path.dirname(sys.executable), "config.json")
        )
    return resource_path("config.json")


# Convenience accessors for the well-known assets.
def get_image_path(image_name: str) -> str:
    return resource_path("images", image_name)


def get_alert_file_path() -> str:
    return resource_path("data", "allerts.chairRorist")


def get_sound_file_path() -> str:
    return resource_path("data", "sound.wav")


def get_data_file_path() -> str:
    """Return the path of the persistent statistics file."""
    return app_data_path("data.chairRorist")
