"""
Test Web App Locally

This script tests the Streamlit web application locally before deployment.
"""

import subprocess
import time
import webbrowser
import sys
import os

def test_streamlit_app():
    """Test the Streamlit app locally."""

    print("\n" + "="*60)
    print("TESTING STOCKGPT WEB APP LOCALLY")
    print("="*60)

    # Check if streamlit is installed
    try:
        import streamlit
        print("[OK] Streamlit is installed")
    except ImportError:
        print("[ERROR] Streamlit not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"])

    # Check if plotly is installed
    try:
        import plotly
        print("[OK] Plotly is installed")
    except ImportError:
        print("[ERROR] Plotly not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "plotly"])

    print("\n" + "-"*60)
    print("Starting Streamlit app...")
    print("-"*60)
    print("\nThe app will open in your browser automatically.")
    print("If it doesn't, navigate to: http://localhost:8501")
    print("\nPress Ctrl+C to stop the server")
    print("-"*60)

    # Start the Streamlit app
    try:
        # Open browser after 3 seconds
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:8501')

        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])

    except KeyboardInterrupt:
        print("\n\n[INFO] Streamlit server stopped")
    except Exception as e:
        print(f"\n[ERROR] Failed to start Streamlit: {e}")

if __name__ == "__main__":
    test_streamlit_app()