import os
import time
from pystray import Icon, MenuItem, Menu
from PIL import Image
from windowsMessage import sendWarning, get_data_file_path, get_image_path
import threading
import status
import sys
import subprocess
import struct
import logger

shutdown_event = threading.Event()

ignored = "Ignored: " + str(status.get_ignored_notifications())
respected = "Respected: " + str(status.get_realised_notifications())

muteText = "Mute"

global_ser = None


def tray_thread(ser):
    global icon
    global global_ser
    global_ser = ser

    icon = Icon(
        "ChairRorist",
        Image.open(get_image_path("sitting.ico")),
        menu=Menu(
            MenuItem(lambda text: ignored, None, enabled=False),
            MenuItem(lambda text: respected, None, enabled=False),
            # MenuItem("Stop", toggle_timer), TODO
            Menu.SEPARATOR,
            MenuItem(lambda text: muteText, toggle_mute),
            MenuItem("Show Warning", sendWarning),
            MenuItem("Reset", lambda icon, item: reset_timer(icon, item, ser)),
            MenuItem("Exit", exit_app),
        ),
    )
    threading.Thread(target=update, daemon=True).start()
    icon.run()


def toggle_mute(icon, item):
    global muteText
    muteText = "Mute" if status.get_muted() else "Unmute"
    status.set_muted(not status.get_muted())


def update_icon():
    """Updates tray icon image"""

    if status.get_sitting_time() == 0:
        icon_path = get_image_path("standing.ico")
    elif status.get_sitting_time() > status.get_alert_interval():
        icon_path = get_image_path("exploding.ico")
    else:
        icon_path = get_image_path("sitting.ico")

    try:
        icon.icon = Image.open(icon_path)
    except Exception as e:
        logger.logger.error(f"Error! Failed to load {icon_path}: {e}")


def update():
    """Updates tray icon"""

    while not status.get_connected():  # Waits for first valid data
        logger.logger.debug("Waiting for USB connection...")
        time.sleep(2)

    logger.logger.info("Connected to sensor")

    # Load initial data from file
    ignoredIn, realisedIn = load_data()
    status.set_ignored_notifications(ignoredIn)
    status.set_realised_notifications(realisedIn)

    while True:
        update_icon()
        if status.get_sitting_time() > 0:
            icon.title = f"Sitting time: {status.get_sitting_time_formatted()}"
        else:
            icon.title = "You are standing!"

        # Use current status values instead of reloading from file
        global ignored
        global respected

        ignored = "Ignored: " + str(status.get_ignored_notifications())
        respected = "Respected: " + str(status.get_realised_notifications())

        icon.update_menu()
        logger.logger.debug("Tray icon updated")

        time.sleep(status.get_polling_interval())


def exit_app(icon, item):
    shutdown_event.set()
    icon.stop()
    if global_ser:
        try:
            global_ser.close()
        except:
            pass
    sys.exit(0)


def reset_timer(icon, item, ser):
    """Zamyka aplikację i ponownie ją uruchamia."""

    ser.close()
    python = sys.executable  # Ścieżka do aktualnie używanego interpretera Pythona
    script = sys.argv[0]  # Aktualnie uruchomiony skrypt

    icon.stop()  # Zamyka ikonę w trayu
    subprocess.Popen([python, script])  # Uruchamia nową instancję skryptu
    sys.exit(0)  # Kończy bieżącą instancję aplikacji


def load_data():
    path = get_data_file_path()
    if not os.path.exists(path):
        return (0, 0)
    with open(path, "rb") as f:
        data = f.read(8)
        if len(data) != 8:
            return (0, 0)
        try:
            return struct.unpack("ii", data)
        except struct.error:
            return (0, 0)


# def toggle_timer():
#     """Zatrzymuje i uruchamia ponownie timer"""
#     sys.exit(0)  # Kończy bieżącą instancję aplikacji
