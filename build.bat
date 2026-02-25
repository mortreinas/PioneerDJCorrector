@echo off
REM Build Pioneer DJ Corrector executable
REM Requires: pip install pyinstaller (or pip install -e ".[build]")

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo Creating venv...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -e .
pip install -q pyinstaller Pillow

echo Creating favicon.ico...
python -c "from PIL import Image; i=Image.open('favicon.png'); i.save('favicon.ico', format='ICO', sizes=[(256,256),(48,48),(32,32),(16,16)])"

echo Building executable...
pyinstaller PioneerDJCorrector.spec --noconfirm

echo.
echo Done. Executable in dist\ folder.
pause
