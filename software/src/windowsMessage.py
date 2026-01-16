from plyer import notification
from winotify import Notification, audio
import os
import sys
import random
import status
import struct
import winsound  # do dźwięku
import status
import logger


def get_allerts_file_path():
    if getattr(sys, "frozen", False):
        # EXE uruchomiony, dane są w _MEIPASS
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        data_path = os.path.join(base_path, "data", "allerts.chairRorist")
    else:
        # Skrypt uruchomiony z software/src/, dane są w ../../data/
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_path, "..", "..", "data", "allerts.chairRorist")

    return os.path.abspath(data_path)


def get_sound_file_path():
    if getattr(sys, "frozen", False):
        # EXE uruchomiony, dane są w _MEIPASS
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        data_path = os.path.join(base_path, "data", "sound.wav")
    else:
        # Skrypt uruchomiony z software/src/, dane są w ../../data/
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_path, "..", "..", "data", "sound.wav")

    return os.path.abspath(data_path)


def get_data_file_path():

    if getattr(sys, "frozen", False):  # .exe
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.abspath(os.path.join(base_path, "data", "data.chairRorist"))
    else:  # .py
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(
            os.path.join(base_path, "..", "..", "data", "data.chairRorist")
        )


def get_image_path(image_name):
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base_path, "images", image_name)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, "..", "..", "images", image_name)


def save_data(int1, int2):
    import tempfile

    path = get_data_file_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=os.path.dirname(path), delete=False) as f:
        f.write(struct.pack("ii", int1, int2))
        temp_path = f.name
    os.replace(temp_path, path)


def randomAllertLine(filename=get_allerts_file_path()):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = sum(1 for _ in f)

        if lines == 0:
            return "File empty"

        id = random.randint(0, lines - 1)

        with open(filename, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == id:
                    return line.strip()

    except FileNotFoundError:
        return "Cannot find file"


def sendWarning():
    """Wysyła warninga z czasem jako powiadomienie windowsa"""

    if not status.get_muted():
        notify(
            randomAllertLine(), f"Sitting time {status.get_sitting_time_formatted()}"
        )
    if status.get_sitting_time() > status.get_alert_interval() * 1.1:
        current = status.get_ignored_notifications()
        status.set_ignored_notifications(current + 1)
        save_data(current + 1, status.get_realised_notifications())


def notify(title: str, message: str, icon_path: str = "images/Exploding.ico"):
    if not icon_path.startswith("images/"):
        icon_full_path = icon_path
    else:
        icon_name = icon_path.split("/", 1)[1] if "/" in icon_path else icon_path
        icon_full_path = get_image_path(icon_name)

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
        winsound.PlaySound(get_sound_file_path(), winsound.SND_FILENAME)

    except Exception as e:
        logger.logger.warning(f"Error playing sound: {e}")


def DEPRECATED_notify(
    title,
    message,
):
    """Wysyła powiadomienie do użytkownika"""
    notification.notify(
        title=title,
        message=message,
        app_name="ChairRorist",
        app_icon=os.path.abspath("images/Exploding.ico"),
        timeout=1,
        toast=True,
    )
