@echo off
echo ======================================
echo Starting StockGPT Pattern Analyzer
echo ======================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing Streamlit...
    pip install streamlit plotly
)

REM Run the app
echo.
echo Starting web app on http://localhost:8501
echo Press Ctrl+C to stop
echo.
python -m streamlit run streamlit_app.py --server.port 8501 --server.address localhost

pause