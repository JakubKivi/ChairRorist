# Ścieżka do pliku main.py
SRC = .\software\src\ChairRorist.py

# Ścieżka do ikony
ICON = .\images\sitting.ico

# Komenda do budowania .exe
execMachen:
	pyinstaller --onefile --hidden-import plyer.platforms.win.notification --clean --noconsole --icon=$(ICON) $(SRC)

