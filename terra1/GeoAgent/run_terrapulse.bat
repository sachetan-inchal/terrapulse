@echo off
title TerraPulse - Earth Observation & AI Investigator
cd /d "%~dp0..\.."
echo =====================================================================
echo           STARTING TERRAPULSE SATELLITE INTELLIGENCE
echo =====================================================================
echo.
echo Launching Backend & Serving Explorer + AI Investigator on http://localhost:8000...
set "PYTHONPATH=%CD%"

start "" "http://localhost:8000"

"%~dp0.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause

