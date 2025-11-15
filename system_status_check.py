"""
Complete System Status Check
Shows what's working and what needs to be done
"""

import sys
# Set encoding to UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import asyncio
import os
from datetime import date, timedelta
from pathlib import Path

async def check_system():
    print("\n" + "="*70)
    print("STOCKGPT SYSTEM STATUS CHECK")
    print("="*70)

    results = {
        "working": [],
        "needs_setup": [],
        "missing": []
    }

    # 1. Check Core Architecture
    print("\n1. CORE ARCHITECTURE")
    print("-" * 40)
    try:
        from stockgpt.core.interfaces import IModel, IDataProvider
        from stockgpt.core.entities import Signal, Stock, Pattern
        print("[OK] Core interfaces loaded")
        print("[OK] Domain entities loaded")
        results["working"].append("Core architecture")
    except ImportError as e:
        print("[X] Core architecture missing:", e)
        results["missing"].append("Core architecture")

    # 2. Check Real Data Provider
    print("\n2. REAL MARKET DATA")
    print("-" * 40)
    try:
        from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider
        provider = MarketDataProvider()

        # Test connection
        connected = await provider.check_connection()
        if connected:
            print("[OK] Market data provider connected (Yahoo Finance)")

            # Fetch real price
            prices = await provider.get_prices("AAPL", days=5)
            if prices:
                latest = prices[-1]
                print(f"[OK] Real-time data working: AAPL ${latest.close:.2f}")
                results["working"].append("Real market data")

            # Get technical indicators
            features = await provider.get_technical_features("SPY")
            if features:
                print(f"[OK] Technical indicators: RSI={features.get('rsi_14', 0):.2f}")
                results["working"].append("Technical analysis")
        else:
            print("[X] Cannot connect to market data")
            results["needs_setup"].append("Market data connection")

    except ImportError:
        print("[X] Market data provider not found")
        results["missing"].append("Market data provider")
    except Exception as e:
        print(f"[X] Error with market data: {e}")
        results["needs_setup"].append("Market data provider")

    # 3. Check Pattern Detection
    print("\n3. AIv3 PATTERN DETECTION")
    print("-" * 40)
    try:
        from aiv3.core.consolidation_tracker import ConsolidationTracker

        # Test pattern detection
        tracker = ConsolidationTracker("TEST")
        print("[OK] Pattern detection system loaded")
        print("[OK] Consolidation tracker ready")
        print("  - Qualification: BBW<30%, ADX<32, Volume<35%")
        print("  - Phases: QUALIFYING -> ACTIVE -> COMPLETED")
        results["working"].append("Pattern detection")

    except ImportError:
        print("[X] Pattern detection not found")
        results["missing"].append("Pattern detection")

    # 4. Check ML Model
    print("\n4. MACHINE LEARNING MODEL")
    print("-" * 40)
    try:
        from stockgpt.infrastructure.ml.xgboost_model import XGBoostModel

        model_path = Path("./models/aiv3_pattern_model.pkl")
        if model_path.exists():
            model = XGBoostModel(str(model_path))
            print("[OK] Trained model found and loaded")
            results["working"].append("ML model")
        else:
            print("[X] No trained model found")
            print("  -> Need to train model with historical data")
            print("  -> Run: python train_model.py")
            results["needs_setup"].append("ML model training")

    except ImportError:
        print("[X] XGBoost model not found")
        results["missing"].append("ML model")

    # 5. Check Backend API
    print("\n5. BACKEND API")
    print("-" * 40)
    if Path("backend/app/main.py").exists():
        print("[OK] FastAPI backend found")
        print("  -> To start: cd backend && uvicorn app.main:app --reload")
        print("  -> API docs: http://localhost:8000/docs")

        # Check if .env exists
        if Path("backend/.env").exists():
            print("[OK] Environment configuration found")
            results["working"].append("Backend API")
        else:
            print("[X] Missing backend/.env file")
            print("  -> Copy from .env.example and configure")
            results["needs_setup"].append("Backend configuration")
    else:
        print("[X] Backend not found")
        results["missing"].append("Backend API")

    # 6. Check Frontend
    print("\n6. FRONTEND")
    print("-" * 40)
    if Path("frontend/package.json").exists():
        print("[OK] React frontend found")
        print("  -> To start: cd frontend && npm install && npm start")
        print("  -> UI: http://localhost:3000")

        if Path("frontend/node_modules").exists():
            print("[OK] Dependencies installed")
            results["working"].append("Frontend")
        else:
            print("[X] Dependencies not installed")
            print("  -> Run: cd frontend && npm install")
            results["needs_setup"].append("Frontend dependencies")
    else:
        print("[X] Frontend not found")
        results["missing"].append("Frontend")

    # 7. Check Database
    print("\n7. DATABASE")
    print("-" * 40)
    if Path("backend/app/models").exists():
        print("[OK] Database models found")
        print("  Options:")
        print("  - PostgreSQL: postgresql://user:pass@localhost/stockgpt")
        print("  - SQLite: sqlite:///./stockgpt.db (easier)")
        results["working"].append("Database models")
    else:
        print("[X] Database models not found")
        results["missing"].append("Database")

    # FINAL SUMMARY
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    print(f"\n[OK] WORKING ({len(results['working'])} components):")
    for item in results["working"]:
        print(f"  - {item}")

    if results["needs_setup"]:
        print(f"\n[!] NEEDS SETUP ({len(results['needs_setup'])} items):")
        for item in results["needs_setup"]:
            print(f"  - {item}")

    if results["missing"]:
        print(f"\n[FAIL] MISSING ({len(results['missing'])} items):")
        for item in results["missing"]:
            print(f"  - {item}")

    # Overall status
    total = len(results["working"]) + len(results["needs_setup"]) + len(results["missing"])
    working_pct = (len(results["working"]) / total * 100) if total > 0 else 0

    print(f"\nOVERALL STATUS: {working_pct:.0f}% Complete")

    if working_pct == 100:
        print("[SUCCESS] System is FULLY OPERATIONAL!")
    elif working_pct >= 60:
        print("[OK] Core system is working. Some setup needed for full features.")
    else:
        print("[!] System needs additional setup.")

    # What can you do now?
    print("\n" + "="*70)
    print("WHAT YOU CAN DO RIGHT NOW")
    print("="*70)

    if "Real market data" in results["working"]:
        print("\n[OK] Fetch real stock prices:")
        print("  python test_real_data.py")

    if "Pattern detection" in results["working"]:
        print("\n[OK] Detect consolidation patterns:")
        print("  python example_usage.py")

    if "Backend API" in results["working"]:
        print("\n[OK] Run API server:")
        print("  cd backend && uvicorn app.main:app --reload")

    if "ML model training" in results["needs_setup"]:
        print("\n[!] To enable AI predictions, train the model:")
        print("  See: RUN_SYSTEM_GUIDE.md section 'Train ML Model'")

    print("\n" + "="*70)
    print("For full setup instructions: See RUN_SYSTEM_GUIDE.md")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(check_system())