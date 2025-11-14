@echo off
REM StockGPT Simple Deployment - Just double-click this file!
title StockGPT Deployment

echo.
echo ================================================
echo   STOCKGPT DEPLOYMENT
echo ================================================
echo.
echo This will start StockGPT in development mode.
echo.
echo Press any key to continue...
pause >nul

powershell.exe -ExecutionPolicy Bypass -File "%~dp0deploy-simple.ps1" -Development

echo.
pause
