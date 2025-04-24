from plyer import notification
from winotify import Notification, audio
import os
import sys
import random


def get_data_file():
    if getattr(sys, 'frozen', False):
        # EXE uruchomiony z dist/, dane są w ../data/
        base_path = os.path.dirname(sys.executable)
        data_path = os.path.join(base_path, '..', 'data', 'allerts.chairRorist')
    else:
        # Skrypt uruchomiony z software/src/, dane są w ../../data/
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_path, '..', '..', 'data', 'allerts.chairRorist')

    return os.path.abspath(data_path)

def randomAllertLine(filename=get_data_file()):
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



def sendWarning(sitting_time):
    """Wysyła warninga z czasem jako powiadomienie windowsa""" 
    notify(randomAllertLine(), f"Sitting time {sitting_time}")



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