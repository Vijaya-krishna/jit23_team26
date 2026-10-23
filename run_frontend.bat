@echo off
title Energy-Aware Task Scheduler - Interactive Frontend Dashboard
echo =====================================================================
echo  ⚡ Starting Energy-Aware Scheduling Framework Frontend Dashboard
echo =====================================================================
cd /d "%~dp0"
if exist ".venv\Scripts\streamlit.exe" (
    echo [INFO] Using virtual environment Streamlit...
    ".venv\Scripts\streamlit.exe" run frontend/streamlit_app.py --server.port 8501
) else (
    echo [INFO] Using system Streamlit...
    streamlit run frontend/streamlit_app.py --server.port 8501
)
pause
