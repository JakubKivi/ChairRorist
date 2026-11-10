"""Windows notifications and alert handling for ChairRorist."""
import os
import random
import struct
import tempfile
from typing import Optional, Tuple, TYPE_CHECKING

import winsound

from . import logging_setup, paths

if TYPE_CHECKING:
    from .status import StatusManager

logger = logging_setup.get_logger()


def get_random_alert_line(filename: Optional[str] = None) -> str:
    """Return a random, non-empty line from the alerts file."""
    filename = filename or paths.get_alert_file_path()
    try:
        with open(filename, "r", encoding="utf-8") as handle:
            lines = [line.strip() for line in handle if line.strip()]
    except FileNotFoundError:
        return "Cannot find file"

    if not lines:
        return "File empty"
    return random.choice(lines)


def save_data(ignored: int, realised: int) -> None:
    """Atomically persist the notification statistics to disk."""
    path = paths.get_data_file_path()
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(struct.pack("ii", int(ignored), int(realised)))
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def load_data() -> Tuple[int, int]:
    """Load persisted notification statistics (defaults to zero)."""
    path = paths.get_data_file_path()
    try:
        with open(path, "rb") as handle:
            data = handle.read(8)
        if len(data) != 8:
            return (0, 0)
        return struct.unpack("ii", data)
    except (FileNotFoundError, OSError, struct.error):
        return (0, 0)


def notify(title: str, message: str, icon_path: str = "images/Exploding.ico") -> None:
    """Show a Windows toast notification and play an audible cue."""
    from winotify import Notification, audio

    if icon_path.startswith("images/"):
        icon_name = icon_path.split("/", 1)[1] if "/" in icon_path else icon_path
        icon_full_path = paths.get_image_path(icon_name)
    else:
        icon_full_path = icon_path

    toast = Notification(
        app_id="ChairRorist_v0.2",
        title=title,
        msg=message,
        icon=icon_full_path,
    )

    if icon_path == "images/Exploding.ico":
        toast.set_audio(audio.Default, loop=False)
    else:
        toast.set_audio(audio.Silent, loop=False)
    toast.show()

    try:
        winsound.PlaySound(paths.get_sound_file_path(), winsound.SND_FILENAME)
    except Exception as exc:
        logger.warning("Error playing sound: %s", exc)


def send_warning(status: "StatusManager") -> None:
    """Send a standing reminder and update the ``ignored`` counter."""
    if not status.muted:
        notify(
            get_random_alert_line(),
            f"Sitting time {status.sitting_time_formatted}",
        )

    if status.sitting_time > status.alert_interval * 1.1:
        status.increment_ignored_notifications()
        save_data(status.ignored_notifications, status.realised_notifications)
