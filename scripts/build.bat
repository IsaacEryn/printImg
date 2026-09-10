@echo off
cd /d "%~dp0\.."
python -m PyInstaller PrintImg.spec --noconfirm
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)
echo Built dist\PrintImg.exe
