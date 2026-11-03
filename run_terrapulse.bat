@echo off
title TerraPulse - Earth Observation & AI Investigator
cd /d "%~dp0"
echo =====================================================================
echo           STARTING TERRAPULSE SATELLITE INTELLIGENCE
echo =====================================================================
echo.
echo [1/2] Checking Python Virtual Environment...
set "VENV_PY=%~dp0terra1\GeoAgent\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo Python virtual environment not found at %VENV_PY%
    pause
    exit /b 1
)

echo [2/2] Launching Backend & Serving Both Interfaces on http://localhost:8000...
set "PYTHONPATH=%~dp0"

start "" "http://localhost:8000"

"%VENV_PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause

