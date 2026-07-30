@echo off
title Cloud Simulator - Backend API Server
echo ========================================================
echo   ⚡ Starting FastAPI Backend API Server...
echo ========================================================
echo.

cd /d "%~dp0"
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
