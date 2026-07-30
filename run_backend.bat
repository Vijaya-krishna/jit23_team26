@echo off
title Cloud Simulator - Backend API Server
echo ========================================================
echo   ⚡ Starting FastAPI Backend API Server...
echo ========================================================
echo.

cd /d "%~dp0"

echo Freeing port 8000 if previously occupied...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :8000 2^>nul ^| findstr LISTENING 2^>nul') do taskkill /f /pid %%a >nul 2>&1

backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
