"""Global hotkey support (Windows)."""
from collections.abc import Callable

import keyboard


def listen_hotkey(hotkey: str, callback: Callable[[], None]) -> None:
    """Register *hotkey* and block the calling thread until it is pressed."""
    keyboard.add_hotkey(hotkey, callback)
    keyboard.wait()
