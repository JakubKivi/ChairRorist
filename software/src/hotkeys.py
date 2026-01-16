import keyboard
from typing import Callable


def execute_callbacks(callback1: Callable[[], None], callback2: Callable[[], None]) -> None:
    """Execute two callback functions in sequence."""
    callback1()
    callback2()


def listen_hotkey(hotkey: str, callback: Callable[[], None], message_function: Callable[[], None]) -> None:
    """Listen for a hotkey and execute callbacks when pressed."""
    keyboard.add_hotkey(hotkey, lambda: execute_callbacks(callback, message_function))
    keyboard.wait()  # blocks only this thread
