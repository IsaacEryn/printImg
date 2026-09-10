@echo off
cd /d "%~dp0\.."
rem .venv가 있으면 그 파이썬으로, 없으면 전역 python으로 빌드한다 (README "빌드" 절과 일치).
if exist .venv\Scripts\python.exe (set PY=.venv\Scripts\python) else (set PY=python)
%PY% -m PyInstaller PrintImg.spec --noconfirm
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)
echo Built dist\PrintImg.exe
