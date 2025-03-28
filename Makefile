# Makefile do budowania pliku .exe za pomocą PyInstaller

# Ścieżka do pliku .py
SRC = .\software\src\main.py

# Ścieżka do ikony
ICON = .\images\sitting.ico

# Komenda do budowania .exe
build:
	pyinstaller --onefile --clean --noconsole --icon=$(ICON) $(SRC)
