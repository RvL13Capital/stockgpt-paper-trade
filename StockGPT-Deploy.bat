@echo off
REM StockGPT Windows One-Click Deployment
REM This script makes deployment as easy as double-clicking!

title StockGPT Deployment Tool
color 0A

echo.
echo ================================================================
echo    STOCKGPT PAPER TRADE TERMINAL - WINDOWS DEPLOYMENT
echo ================================================================
echo.
echo Welcome to the easiest way to deploy StockGPT on Windows!
echo.
echo This script will:
echo   - Check system requirements
echo   - Install Docker if needed
echo   - Set up StockGPT with one click
echo   - Provide easy management options
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is not available on this system.
    echo Please install PowerShell and try again.
    pause
    exit /b 1
)

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Not running as Administrator.
    echo Some features may not work correctly.
    echo It's recommended to run this script as Administrator.
    echo.
    choice /M "Continue anyway" /C YN /N
    if errorlevel 2 (
        echo Please run this script as Administrator.
        pause
        exit /b 1
    )
)

REM Main menu
echo.
echo What would you like to do?
echo.
echo 1. Quick Start (Development Mode)
echo 2. Production Deployment (with SSL)
echo 3. Production with Monitoring
echo 4. Check Status
echo 5. View Logs
echo 6. Stop StockGPT
echo 7. Backup Data
echo 8. Update StockGPT
echo 9. Advanced Options
echo 0. Exit
echo.

set /p choice="Enter your choice (0-9): "

REM Execute the chosen option
if "%choice%"=="1" (
    echo.
    echo Starting StockGPT in Development Mode...
    echo.
    powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Development
) else if "%choice%"=="2" (
    echo.
    echo Starting StockGPT in Production Mode...
    echo.
    powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Production
) else if "%choice%"=="3" (
    echo.
    echo Starting StockGPT in Production Mode with Monitoring...
    echo.
    powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Production -Monitoring
) else if "%choice%"=="4" (
    echo.
    echo Checking StockGPT Status...
    echo.
    powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Status
) else if "%choice%"=="5" (
    echo.
    echo StockGPT Logs
    echo.
    echo Which service logs would you like to view?
    echo 1. All Services
    echo 2. Backend (API)
    echo 3. Frontend (Web Interface)
    echo 4. Database (PostgreSQL)
    echo 5. Redis (Cache)
    echo.
    set /p logchoice="Enter your choice (1-5): "
    
    if "%logchoice%"=="1" (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Logs
    ) else if "%logchoice%"=="2" (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Logs backend
    ) else if "%logchoice%"=="3" (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Logs frontend
    ) else if "%logchoice%"=="4" (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Logs postgres
    ) else if "%logchoice%"=="5" (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Logs redis
    ) else (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Logs
    )
) else if "%choice%"=="6" (
    echo.
    echo Stopping StockGPT...
    echo.
    powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Stop
) else if "%choice%"=="7" (
    echo.
    echo Creating StockGPT Backup...
    echo.
    powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Backup
) else if "%choice%"=="8" (
    echo.
    echo Updating StockGPT...
    echo.
    powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Update
) else if "%choice%"=="9" (
    echo.
    echo Advanced Options
echo.
echo 1. Restart StockGPT
echo 2. Custom Deployment Options
echo 3. Show Help
echo.
    set /p advancedchoice="Enter your choice (1-3): "
    
    if "%advancedchoice%"=="1" (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Restart
    ) else if "%advancedchoice%"=="2" (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1"
    ) else if "%advancedchoice%"=="3" (
        powershell -ExecutionPolicy Bypass -File "windows-deploy.ps1" -Help
    ) else (
        echo Invalid choice.
    )
) else if "%choice%"=="0" (
    echo.
    echo Thank you for using StockGPT!
    echo Visit https://github.com/yourusername/stockgpt for more information.
    echo.
) else (
    echo Invalid choice. Please try again.
)

echo.
echo Press any key to exit...
pause >nul