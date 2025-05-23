from plyer import notification
from winotify import Notification, audio
import os
import sys
import random
import status
import struct


def get_allerts_file_path():
    if getattr(sys, 'frozen', False):
        # EXE uruchomiony z dist/, dane są w ../data/
        base_path = os.path.dirname(sys.executable)
        data_path = os.path.join(base_path, '..', 'data', 'allerts.chairRorist')
    else:
        # Skrypt uruchomiony z software/src/, dane są w ../../data/
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_path, '..', '..', 'data', 'allerts.chairRorist')

    return os.path.abspath(data_path)


def get_data_file_path():
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    if getattr(sys, 'frozen', False):  # .exe
        return os.path.abspath(os.path.join(base_path, '..', 'data', 'data.chairRorist'))
    else:  # .py
        return os.path.abspath(os.path.join(base_path, '..', '..', 'data', 'data.chairRorist'))
    

def save_data(int1, int2):
    path = get_data_file_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(struct.pack('ii', int1, int2))

def randomAllertLine(filename=get_allerts_file_path()):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)

        if lines == 0:
            return "File empty"  

        id = random.randint(0, lines - 1)

        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == id:
                    return line.strip()

    except FileNotFoundError:
        return "Canot find file"



def sendWarning():
    """Wysyła warninga z czasem jako powiadomienie windowsa""" 
    print(status.get_ignored_notifications())
    print(status.get_realised_notifications())

    notify(randomAllertLine(), f"Sitting time {status.get_sitting_time_formatted()}")
    if status.get_sitting_time() > 5400:
        current=status.get_ignored_notifications()
        status.set_ignored_notifications(current+1)
        save_data(current+1, status.get_realised_notifications())


def notify(title: str, message: str, icon_path: str = None):
    toast = Notification(
        app_id="ChairRorist",
        title=title,
        msg=message,
        icon=os.path.abspath("images/Exploding.ico")  # tu możesz podać ścieżkę do ikony, nie pojawi się w trayu
    )
    toast.set_audio(audio.Default, loop=False)
    toast.show()



def DEPRECATED_notify(title, message, ):
    """Wysyła powiadomienie do użytkownika"""
    notification.notify(
        title=title,          
        message=message,
        app_name="ChairRorist",
        app_icon= os.path.abspath("images/Exploding.ico"),
        timeout=1,
        toast=True
    )



    