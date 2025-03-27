import serial
import time
import threading
import windowsMessage as wM
import tray
import status

PORT = "COM5"
BAUDRATE = 9600

time.sleep(5)

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
except Exception as e:
    wM.notify(f"Error", "Failed to connect to sensor.")
    print(f"Error! Failed to connect to: {PORT}: {e}")
    exit(1)

threading.Thread(target=tray.tray_thread, daemon=True).start()

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
                    wM.sendWarning(status.get_sitting_time_formatted())
                    status.set_last_alert_time(time.time())
            else:
                status.stading()

    except Exception as e:
        print(f"Error [2]: {e}")
    if status.get_conntected():
        time.sleep(status.get_polling_interval())
    else:
        time.sleep(3)
