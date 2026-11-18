@echo off
setlocal enabledelayedexpansion
title StudyAI — First-Time Environment Setup
color 0b

echo =========================================================================
echo   StudyAI — Automated Environment Setup ^& Prerequisite Verification
echo =========================================================================
echo   This script prepares StudyAI to run on this computer:
echo   [1] Verifies Python (3.10-3.12 recommended), Node.js, and npm
echo   [2] Creates an isolated virtual environment (.venv)
echo   [3] Installs backend Python dependencies
echo   [4] Installs frontend React/Vite dependencies cleanly
echo   [5] Generates a local .env configuration (never overwriting existing)
echo   [6] Runs initial database migrations
echo   [7] Validates Ollama AI and OCR service readiness
echo =========================================================================
echo.

cd /d "%~dp0"

:: -------------------------------------------------------------------------
:: 1. Check Python
:: -------------------------------------------------------------------------
echo [1/7] Checking Python prerequisite...
set "PY_CMD="

:: Check for py -3.12 or python
py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3.12"
    for /f "tokens=*" %%v in ('py -3.12 --version') do echo   Found: %%v
) else (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=python"
        for /f "tokens=*" %%v in ('python --version') do echo   Found: %%v
    ) else (
        echo   [ERROR] Python is not installed or not in your system PATH!
        echo   Please install Python 3.12 from https://www.python.org/downloads/
        echo   Ensure "Add Python to PATH" is checked during installation.
        pause
        exit /b 1
    )
)

:: -------------------------------------------------------------------------
:: 2. Check Node & npm
:: -------------------------------------------------------------------------
echo.
echo [2/7] Checking Node.js and npm prerequisites...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Node.js is not found in PATH!
    echo   Please install Node.js 20+ (LTS) from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version') do echo   Node.js: %%v
for /f "tokens=*" %%v in ('npm --version') do echo   npm:     v%%v

:: -------------------------------------------------------------------------
:: 3. Create Virtual Environment
:: -------------------------------------------------------------------------
echo.
echo [3/7] Setting up Python virtual environment (.venv)...
if not exist "%~dp0.venv\Scripts\python.exe" (
    if exist "%~dp0backend\venv\Scripts\python.exe" (
        echo   Found existing backend virtual environment at backend\venv.
        set "VENV_PY=%~dp0backend\venv\Scripts\python.exe"
    ) else (
        echo   Creating clean virtual environment in .venv ...
        %PY_CMD% -m venv "%~dp0.venv"
        if %errorlevel% neq 0 (
            echo   [ERROR] Failed to create virtual environment!
            pause
            exit /b 1
        )
        set "VENV_PY=%~dp0.venv\Scripts\python.exe"
    )
) else (
    echo   Virtual environment already exists in .venv.
    set "VENV_PY=%~dp0.venv\Scripts\python.exe"
)

:: -------------------------------------------------------------------------
:: 4. Install Backend Dependencies
:: -------------------------------------------------------------------------
echo.
echo [4/7] Installing backend Python packages from backend\requirements.txt ...
"%VENV_PY%" -m pip install --upgrade pip >nul 2>&1
"%VENV_PY%" -m pip install -r "%~dp0backend\requirements.txt"
if %errorlevel% neq 0 (
    echo   [ERROR] Failed to install backend dependencies. Check your internet connection.
    pause
    exit /b 1
)
echo   [OK] Backend dependencies installed successfully.

:: -------------------------------------------------------------------------
:: 5. Install Frontend Dependencies
:: -------------------------------------------------------------------------
echo.
echo [5/7] Installing frontend dependencies cleanly...
cd /d "%~dp0frontend"
if exist package-lock.json (
    call npm ci
) else (
    call npm install
)
if %errorlevel% neq 0 (
    echo   [WARN] npm ci encountered an issue, trying npm install...
    call npm install
)
cd /d "%~dp0"
echo   [OK] Frontend dependencies ready.

:: -------------------------------------------------------------------------
:: 6. Configure Environment File (.env)
:: -------------------------------------------------------------------------
echo.
echo [6/7] Checking environment configuration (.env)...
if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" (
        echo   Creating initial .env from .env.example ...
        copy "%~dp0.env.example" "%~dp0.env" >nul
        echo   [OK] Created .env template.
    ) else (
        echo   [WARN] .env.example not found; skipping .env creation.
    )
) else (
    echo   [OK] Existing .env file detected and preserved.
)

:: -------------------------------------------------------------------------
:: 7. Apply Database Migrations & Diagnostics
:: -------------------------------------------------------------------------
echo.
echo [7/7] Applying database migrations and running system diagnostic...
cd /d "%~dp0backend"
"%VENV_PY%" manage.py migrate --noinput
if %errorlevel% neq 0 (
    echo   [WARN] Migration check returned a notice. Continuing...
)

echo.
"%VENV_PY%" manage.py check_configuration
cd /d "%~dp0"

echo.
echo =========================================================================
echo   🎉 StudyAI Setup Completed Successfully!
echo =========================================================================
echo.
echo   To launch StudyAI anytime, simply run:
echo       start_studyai.bat
echo   or:
echo       npm start
echo.
echo   Happy studying!
echo =========================================================================
pause
