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
    """Return a user-writable data path, kept separate for dev vs. build.

    The packaged executable persists to the user's app-data directory, while
    running from source persists under ``data/dev/`` so that development
    testing never touches real production statistics or settings.
    """
    if is_frozen():
        base = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME
        )
    else:
        base = resource_path("data", "dev")
    return os.path.abspath(os.path.join(base, *parts))


def config_file_path() -> str:
    """Return the location of the read-only config for the current mode.

    The packaged executable always uses ``config.production.json`` (a fixed
    60-minute alert interval), while running from source uses ``config.json``
    so the alert/polling intervals can be tuned for testing.
    """
    name = "config.production.json" if is_frozen() else "config.json"
    return resource_path(name)


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
