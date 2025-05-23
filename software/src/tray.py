import os
import time
from pystray import Icon, MenuItem, Menu
from PIL import Image
from windowsMessage import sendWarning, get_data_file_path
import threading
import status
import sys
import subprocess
import struct

ignored = "Ignored: "+str(status.get_ignored_notifications())
respected = "Respected: "+str(status.get_realised_notifications())

def tray_thread(ser):
    global icon
    
    icon = Icon("ChairRorist", Image.open("images/Sitting.ico"), menu=Menu( 
        MenuItem(lambda text: ignored, None, enabled=False),
        MenuItem(lambda text: respected , None, enabled=False),
        # MenuItem("Stop", toggle_timer), TODO
        Menu.SEPARATOR,
        MenuItem("Show Warning", sendWarning), 
        MenuItem("Reset", lambda icon, item: reset_timer(icon, item, ser)), 
        MenuItem("Exit", exit_app)
        )
    )
    threading.Thread(target=update, daemon=True).start()
    icon.run()



def update_icon():
    """Updates tray icon image"""

    if status.get_sitting_time() == 0:
        icon_path = os.path.abspath("images/standing.ico")
    elif status.get_sitting_time() > status.get_alert_interval():
        icon_path = os.path.abspath("images/exploding.ico")
    else:
        icon_path = os.path.abspath("images/sitting.ico")

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

        ignoredIn, realisedIn = load_data()
        status.set_ignored_notifications(ignoredIn)
        status.set_realised_notifications(realisedIn)

        global ignored
        global respected

        ignored = "Ignored: "+str(ignoredIn)
        respected = "Respected: "+str(realisedIn)

        icon.update_menu()
        print("updated")

        time.sleep(status.get_polling_interval())  


def exit_app(icon, item):
    icon.stop()
    os._exit(0)


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
    with open(path, 'rb') as f:
        data = f.read(8)
        if len(data) < 8:
            return (0, 0)
        return struct.unpack('ii', data)

# def toggle_timer():
#     """Zatrzymuje i uruchamia ponownie timer"""
#     sys.exit(0)  # Kończy bieżącą instancję aplikacji
