import serial
import time
from plyer import notification

PORT = "COM5"  # Sprawdź w Menadżerze urządzeń
BAUDRATE = 9600  # Dopasuj do ustawień ATTiny

def notify_user():
    """Wysyła powiadomienie do użytkownika"""
    notification.notify(
        title="Podnosimy dupsko!",
        message=f"Siedzisz już od {sitting_time_formated}",
        app_name="ChairRorist",
        timeout=10
    )

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
except Exception as e:
    print(f"Błąd połączenia z {PORT}: {e}")
    notify_user()
    exit(1)

sitting_time = 1800
sitting_time_formated=""
polling_interval = 2#180  # 3 minuty
alert_interval = 10#3600   # 1 godzina
last_alert_time = time.time()  # Zapamiętanie czasu ostatniego powiadomienia

while True:
    try:
        ser.write(b"?")  # Opcjonalne - jeśli ATTiny czeka na sygnał
        state = ser.readline().strip()  # Odczyt linii z ATTiny
        if state:
            state = int(state)
            if state == 0:  # Siedzenie
                sitting_time += polling_interval

                hours, remainder = divmod(sitting_time, 3600)
                minutes, _ = divmod(remainder, 60)

                sitting_time_formated = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

                if time.time() - last_alert_time >= alert_interval:
                    notify_user()
                    last_alert_time = time.time()
            else:  # Stanie
                sitting_time = 0  # Reset
                last_alert_time = time.time()  # Reset timera powiadomień

    except Exception as e:
        print(f"Błąd odczytu: {e}")

    time.sleep(polling_interval)
