
import os
import time
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading
import status
import sys
import subprocess

def tray_thread():
    global icon
    icon = Icon("ChairRorist", Image.open("images/Sitting.ico"), menu=Menu(MenuItem("Reset", reset_timer), MenuItem("Exit", exit_app)))
    threading.Thread(target=update, daemon=True).start()
    icon.run()


def update_icon():
    """Updates tray icon image"""

    if status.get_sitting_time() == 0:
        icon_path = os.path.abspath("images/Standing.ico")
    elif status.get_sitting_time() > status.get_alert_interval():
        icon_path = os.path.abspath("images/Exploding.ico")
    else:
        icon_path = os.path.abspath("images/Sitting.ico")

    try:
        icon.icon = Image.open(icon_path)  
    except Exception as e:
        print(f"Error! Failed to load {icon_path}: {e}")

def update():
    """Updates tray icon"""

    while not status.get_conntected():  # Waits for first valid data
        print("Waiting for USB...")
        time.sleep(2)

    print("Connected")

    while True:
        update_icon()
        if status.get_sitting_time() > 0:
            icon.title = f"Sitting time: {status.get_sitting_time_formatted()}"
        else:
            icon.title = "You are standing!"
        time.sleep(status.get_polling_interval())  

def exit_app(icon, item):
    icon.stop()
    os._exit(0)

def reset_timer():
    """Zamyka aplikację i ponownie ją uruchamia."""
    python = sys.executable  # Ścieżka do aktualnie używanego interpretera Pythona
    script = sys.argv[0]  # Aktualnie uruchomiony skrypt

    icon.stop()  # Zamyka ikonę w trayu
    subprocess.Popen([python, script])  # Uruchamia nową instancję skryptu
    sys.exit(0)  # Kończy bieżącą instancję aplikacji