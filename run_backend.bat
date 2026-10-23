@echo off
title Energy-Aware Task Scheduler - Backend REST API Server
echo =====================================================================
echo  ⚡ Starting Energy-Aware Scheduling Framework Backend REST API
echo =====================================================================
cd /d "%~dp0backend"
if exist "..\.venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment Python...
    start http://localhost:8000/docs
    "..\.venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo [INFO] Using system Python...
    start http://localhost:8000/docs
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
)
pause
