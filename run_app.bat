@echo off
title Cloud Simulator Launcher
echo ========================================================
echo   ⚡ Starting Energy-Aware Cloud Simulator Platform...
echo ========================================================
echo.

cd /d "%~dp0"

echo Freeing port 8000 if previously occupied...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :8000 2^>nul ^| findstr LISTENING 2^>nul') do taskkill /f /pid %%a >nul 2>&1

echo [1/2] Launching Backend Server on http://localhost:8000 ...
start "Cloud Simulator - Backend API" cmd /k "cd /d %~dp0 && backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Frontend UI on http://localhost:5173 ...
start "Cloud Simulator - Frontend UI" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening browser...
start http://localhost:5173/

echo.
echo ========================================================
echo   ✅ Application launched successfully!
echo   - Frontend UI:  http://localhost:5173/
echo   - Backend API:   http://localhost:8000/docs
echo   - Login Account: admin / AdminPass123!
echo ========================================================
echo.
