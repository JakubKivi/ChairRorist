# ChairRorist

<img align="left" width="400" height="400" src="images/ChairRoristHardware.webp">

This is a simple Python app that connects to an Arduino with a distance sensor to track if your height-adjustable desk is up or down. It sits quietly in the system tray and reminds you to stand every hour.

More info [here](https://jakubkivi.github.io#portfolio-modal-ChairRorist)

## Features

- Real-time desk position monitoring via Arduino sensor
- System tray integration with status indicators
- Configurable alert intervals and polling rates
- Hotkey support for timer reset
- Persistent statistics tracking
- Windows notifications with custom alerts
- Comprehensive logging

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/JakubKivi/ChairRorist.git
   cd ChairRorist
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Configure settings in `config.json`

4. Build the executable:
   ```bash
   make build
   ```

## Configuration

The application can be configured via `config.json`:

```json
{
  "serial": {
    "port": "COM3",
    "baudrate": 9600,
    "timeout": 1
  },
  "intervals": {
    "polling": 5,
    "alert": 3600
  },
  "hotkeys": {
    "reset_timer": "ctrl+shift+alt+d"
  }
}
```

## Usage

1. Upload the Arduino sketch from `hardware/ChairRorist/` to your Arduino
2. Run the application
3. The app will appear in your system tray
