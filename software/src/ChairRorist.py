import serial
import time
import threading
import windowsMessage as wM
import tray
import status
import hotkeys
import config
import logger
import atexit

PORT = config.config.get("serial.port", "COM3")
BAUDRATE = config.config.get("serial.baudrate", 9600)
TIMEOUT = config.config.get("serial.timeout", 1)

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
    logger.logger.info(f"Connected to serial port {PORT} at {BAUDRATE} baud")
    atexit.register(lambda: ser.close())
except Exception as e:
    wM.notify(f"Error", f"Failed to connect to sensor on {PORT}.")
    logger.logger.error(f"Failed to connect to: {PORT}: {e}")
    exit(1)

threading.Thread(target=tray.tray_thread, args=(ser,), daemon=True).start()
threading.Thread(
    target=hotkeys.listen_hotkey,
    args=(
        config.config.get("hotkeys.reset_timer", "ctrl+shift+alt+d"),
        lambda: wM.notify(
            "Timer Reset", "Sitting timer has been reset.", "images/standing.ico"
        ),
        lambda: tray.reset_timer(tray.icon, None, ser),
    ),
    daemon=True,
).start()

while not tray.shutdown_event.is_set():
    try:
        ser.write(b"?")
        state = ser.readline().strip()
        if state:
            # Validate input
            try:
                state_int = int(state)
                if state_int not in (0, 1):
                    logger.logger.warning(f"Invalid state received: {state_int}")
                    continue
                status.set_connected(True)
                if state_int == 0:
                    status.increment()
                    if status.check():
                        wM.sendWarning()
                        status.set_last_alert_time(time.time())
                else:
                    status.standing()
            except ValueError as e:
                logger.logger.error(f"Invalid data from sensor: {state} - {e}")
                continue

    except Exception as e:
        logger.logger.error(f"Error in main loop: {e}")
        status.set_connected(False)
    if status.get_connected():
        time.sleep(status.get_polling_interval())
    else:
        time.sleep(3)
