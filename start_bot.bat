@echo off
setlocal enabledelayedexpansion
title Auto-Attendance Bot Launcher

:: --- MAGIC ANCHOR: Force the script to run in its own folder ---
cd /d "%~dp0"

echo ===================================================
echo       Auto-Attendance Bot Setup ^& Launcher 
echo ===================================================
echo.

:: --- 1. CHECK IF DOCKER IS INSTALLED ---
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Docker is missing from this computer.
    echo [*] Attempting to install Docker Desktop via winget...
    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    
    echo.
    echo ===================================================
    echo [!] DOCKER INSTALLED! A SYSTEM REBOOT IS REQUIRED.
    echo [!] Please restart your computer, then double-click this script again.
    echo ===================================================
    pause
    exit /b
)

:: --- 2. CHECK IF DOCKER IS RUNNING ---
echo [*] Checking Docker engine status...
docker info >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [V] Docker engine is already running!
    goto DOCKER_READY
)

echo [*] Docker is sleeping. Waking it up...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo [*] Waiting for Docker engine to start (this usually takes 10-30 seconds)...

:WAIT_DOCKER
timeout /t 5 /nobreak >nul
docker info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo    ...still waiting for Docker...
    goto WAIT_DOCKER
)
echo [V] Docker engine is fully online!

:DOCKER_READY
echo.

:: --- 3. START N8N AND EVOLUTION API ---
echo [*] Booting up n8n and WhatsApp API...
cd local-browser-bridge
call docker-compose up -d
cd ..
echo [V] Background services are live!
echo.

:: --- 4. PREPARE THE PYTHON ENVIRONMENT ---
echo [*] Preparing the Python Bot...
cd python-bot

if not exist "venv\" (
    echo [*] First-time setup: Creating Python virtual environment...
    python -m venv venv
)

echo [*] Activating environment and checking dependencies...
call venv\Scripts\activate
pip install flask playwright >nul 2>&1
playwright install chromium >nul 2>&1
echo [V] Python environment ready!
echo.

:: --- 5. LAUNCH THE APP ---
echo ===================================================
echo        🚀 ALL SYSTEMS GO! LAUNCHING BOT...
echo ===================================================
echo [*] Opening Control Panel in your web browser...
timeout /t 2 /nobreak >nul
start http://localhost:5000

echo [*] DO NOT CLOSE THIS WINDOW while you are attending classes!
python app.py

pause