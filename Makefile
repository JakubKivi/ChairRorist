# Ścieżka do pliku main.py
SRC = .\software\src\ChairRorist.py

# Ścieżka do ikony
ICON = .\images\sitting.ico

SHELL = cmd.exe

# Komenda do budowania .exe
build:
	pyinstaller ChairRorist.spec

# Uruchom testy
test:
	python -m pytest tests/ -v

# Zainstaluj zależności
install:
	pip install -r requirements.txt

# Wyczyść pliki tymczasowe
clean:
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist

