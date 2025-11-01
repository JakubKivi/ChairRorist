import serial
import time
import threading
import windowsMessage as wM
import tray
import status
import hotkeys

PORT = "COM3"
BAUDRATE = 9600

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
except Exception as e:
    wM.notify(f"Error", "Failed to connect to sensor.")
    print(f"Error! Failed to connect to: {PORT}: {e}")
    exit(1)

threading.Thread(target=tray.tray_thread, args=(ser,), daemon=True).start()
threading.Thread(
    target=hotkeys.listen_hotkey,
    args=(
        "ctrl+shift+alt+d",
        lambda: tray.reset_timer(tray.icon, None, ser),
        lambda: wM.notify("Timer Reset", "Sitting timer has been reset."),
    ),
    daemon=True,
).start()

while True:
    try:
        ser.write(b"?")
        state = ser.readline().strip()
        if state:
            status.set_connected(True)
            state = int(state)
            if state == 0:
                status.increment()
                if status.check():
                    wM.sendWarning()
                    status.set_last_alert_time(time.time())
            else:
                status.stading()

    except Exception as e:
        print(f"Error [2]: {e}")
    if status.get_conntected():
        time.sleep(status.get_polling_interval())
    else:
        time.sleep(3)
