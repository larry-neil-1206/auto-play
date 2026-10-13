@echo off
setlocal
cd /d "%~dp0"

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller is not installed. Run: python -m pip install pyinstaller
    exit /b 1
)

python -m PyInstaller --noconfirm --clean --onefile --console --name autoplay --specpath build --distpath dist --workpath build\work --add-data "..\sequences\example.json;sequences" autoplay\__main__.py
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo Updated executable: dist\autoplay.exe