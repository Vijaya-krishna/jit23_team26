@echo off
title Cloud Simulator - Frontend UI Server
echo ========================================================
echo   ⚡ Starting Vite Frontend UI Server...
echo ========================================================
echo.

cd /d "%~dp0frontend"
npm run dev

pause
