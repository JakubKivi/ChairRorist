from plyer import notification
from winotify import Notification, audio
import os

def sendWarning(sitting_time):
    """Wysyła warninga z czasem jako powiadomienie windowsa"""          #TODO Jakieś fajne teksty czy coś XD
    notify("Lift your ass!", f"Sitting time {sitting_time}")



def notify(title: str, message: str, icon_path: str = None):
    toast = Notification(
        app_id="ChairRorist",
        title=title,
        msg=message,
        icon=os.path.abspath("images/Exploding.ico")  # tu możesz podać ścieżkę do ikony, nie pojawi się w trayu
    )
    toast.set_audio(audio.Default, loop=False)
    toast.show()
    print("dupa")



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