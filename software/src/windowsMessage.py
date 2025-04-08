from plyer import notification
import os

def sendWarning(sitting_time):
    """Wysyła warninga z czasem jako powiadomienie windowsa"""          #TODO Jakieś fajne teksty czy coś XD
    notify("Lift your ass!", f"Sitting time {sitting_time}")


def notify(title, message, ):
    """Wysyła powiadomienie do użytkownika"""
    notification.notify(
        title=title,          
        message=message,
        app_name="ChairRorist",
        app_icon= os.path.abspath("images/Exploding.ico"),
        timeout=1,
        toast=True
    )