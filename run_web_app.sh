#!/bin/bash

# Run StockGPT Web App
echo "======================================"
echo "Starting StockGPT Pattern Analyzer"
echo "======================================"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Set environment variables if .env exists
if [ -f ".env" ]; then
    echo "Loading environment variables..."
    export $(cat .env | xargs)
fi

# Run Streamlit app
echo "Starting web app on http://localhost:8501"
echo "Press Ctrl+C to stop"
streamlit run streamlit_app.py --server.port 8501 --server.address localhost