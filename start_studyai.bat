@echo off
title StudyAI — AI Study Analyzer & Personalized Exam Generator
color 0b

echo =========================================================================
echo   StudyAI — Starting Django Backend & React Frontend
echo =========================================================================
echo   Starting StudyAI... Your default web browser will open automatically!
echo.
echo   Press Ctrl+C or close this window to stop the application.
echo =========================================================================
echo.

cd /d "%~dp0"

:: 1. If Node is installed, prefer the unified runner
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Launching StudyAI Unified Service via Node...
    node start_all.js
    goto :done
)

:: 2. Fallback direct execution
set "PY_CMD=python"
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0backend\venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0backend\venv\Scripts\python.exe"
)

echo [1/3] Checking Database Migrations...
cd /d "%~dp0backend"
"%PY_CMD%" manage.py migrate --noinput >nul 2>&1

echo [2/3] Launching Django Backend on port 8000 ...
start "StudyAI Backend (Django)" /min cmd /c "cd /d "%~dp0backend" && "%PY_CMD%" manage.py runserver 127.0.0.1:8000"

echo [3/3] Launching React Frontend on port 5173 ...
cd /d "%~dp0frontend"
start "StudyAI Frontend (React)" /min cmd /c "cd /d "%~dp0frontend" && npx vite --host 127.0.0.1 --port 5173"

echo.
echo =========================================================================
echo   StudyAI is starting up!
echo   - Web App:  http://127.0.0.1:5173/
echo   - Backend:  http://127.0.0.1:8000/
echo   - Admin:    http://127.0.0.1:8000/admin/
echo =========================================================================
echo.
timeout /t 3 >nul
start http://127.0.0.1:5173/

:done
pause
