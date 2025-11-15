# 🚀 Complete Guide to Run StockGPT System

## Prerequisites
- Python 3.8+ installed
- Node.js 16+ installed (for frontend)
- Git installed
- PostgreSQL (optional, for full backend)

## 📥 Step 1: Get the Latest Code

### Option A: Clone Fresh (if starting new)
```bash
git clone https://github.com/RvL13Capital/stockgpt-paper-trade.git
cd stockgpt-paper-trade
```

### Option B: Update Existing (if you already have it)
```bash
git pull origin main
```

## 🔧 Step 2: Set Up Python Environment

### Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Install ALL Dependencies
```bash
# Backend dependencies
pip install -r backend/requirements.txt

# New refactored system dependencies
pip install yfinance pandas numpy xgboost optuna scikit-learn aiohttp joblib

# If requirements.txt is missing, install manually:
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
pip install pydantic email-validator python-multipart python-jose[cryptography]
pip install pandas numpy scikit-learn xgboost yfinance aiohttp
pip install optuna joblib matplotlib seaborn
```

## 🎯 Step 3: Quick Tests (Start Here!)

### A. Test Real Market Data (Simplest)
```bash
python test_real_data.py
```
Expected output:
```
[OK] Connection test: PASSED
[OK] Successfully fetched 4 days of price data
Latest Real Market Data for AAPL:
  Close: $272.95
  RSI(14): 72.24
[SUCCESS] All data is REAL from actual markets!
```

### B. Run Interactive Examples
```bash
python example_usage.py
```
This will:
- Detect patterns in real stocks
- Calculate technical indicators
- Show signal generation examples

## 🏃 Step 4: Run the Full System

### A. Backend API Server

#### 1. Set up environment variables
```bash
# Create .env file in backend folder
cd backend
cp ../.env.example .env

# Edit .env with your settings:
DATABASE_URL=postgresql://user:password@localhost/stockgpt
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key
```

#### 2. Set up database (if using PostgreSQL)
```bash
# Create database
psql -U postgres
CREATE DATABASE stockgpt;
\q

# Run migrations
cd backend
alembic upgrade head
```

#### 3. Start the backend server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### B. Frontend (React)

#### 1. Install frontend dependencies
```bash
cd frontend
npm install
```

#### 2. Configure API endpoint
```bash
# Edit frontend/.env
REACT_APP_API_URL=http://localhost:8000
```

#### 3. Start frontend
```bash
npm start
```

Frontend will be available at: http://localhost:3000

## 🧪 Step 5: Test Specific Components

### A. Pattern Detection System
```python
# Create test_patterns.py
import asyncio
from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider
from aiv3.core.consolidation_tracker import ConsolidationTracker

async def test():
    provider = MarketDataProvider()

    # Get real data
    prices = await provider.get_prices("AAPL", days=100)

    # Detect patterns
    tracker = ConsolidationTracker("AAPL")
    pattern = tracker.update(prices)

    if pattern:
        print(f"Pattern found: {pattern.phase}")
        print(f"Range: ${pattern.lower_boundary:.2f} - ${pattern.upper_boundary:.2f}")

asyncio.run(test())
```

### B. Real-Time Signal Generation
```python
# Create generate_signals.py
import asyncio
from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider

async def generate_signals():
    provider = MarketDataProvider()

    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMD"]

    for symbol in symbols:
        features = await provider.get_technical_features(symbol)

        if features:
            rsi = features.get('rsi_14', 50)

            if rsi > 70:
                print(f"⚠️ {symbol}: OVERBOUGHT (RSI: {rsi:.2f})")
            elif rsi < 30:
                print(f"💚 {symbol}: OVERSOLD - Potential Buy (RSI: {rsi:.2f})")
            else:
                print(f"➖ {symbol}: Neutral (RSI: {rsi:.2f})")

asyncio.run(generate_signals())
```

## 🐳 Step 6: Docker Option (All-in-One)

### Build and run with Docker Compose
```bash
# Make sure Docker Desktop is running

# Build all services
docker-compose build

# Start all services
docker-compose up

# Services will be available at:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
```

## 📊 Step 7: Train ML Model (Advanced)

### Train on Historical Data
```python
# Create train_model.py
import asyncio
from datetime import date, timedelta
from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider
from aiv3.ml.model_training_pipeline import ModelTrainingPipeline

async def train():
    provider = MarketDataProvider()
    pipeline = ModelTrainingPipeline(provider)

    # Train on 6 months of data (use 2+ years in production)
    results = await pipeline.train_model(
        symbols=["AAPL", "MSFT", "GOOGL"],
        start_date=date.today() - timedelta(days=180),
        end_date=date.today(),
        optimize_hyperparameters=False  # Set True for better model
    )

    print(f"Training complete!")
    print(f"Patterns found: {results['total_patterns']}")
    print(f"Accuracy: {results['train_accuracy']:.2%}")

asyncio.run(train())
```

## 🔍 Common Issues & Solutions

### Issue 1: ModuleNotFoundError
```bash
# Solution: Install missing module
pip install [missing_module]
```

### Issue 2: Database Connection Error
```bash
# Solution: Use SQLite instead of PostgreSQL
# In .env file:
DATABASE_URL=sqlite:///./stockgpt.db
```

### Issue 3: Port Already in Use
```bash
# Solution: Use different ports
uvicorn app.main:app --port 8001  # Backend
npm start -- --port 3001           # Frontend
```

### Issue 4: API Key Missing
```bash
# Solution: The system works without API keys
# It will use Yahoo Finance (free) as fallback
```

## ✅ Verification Checklist

Run these commands to verify everything works:

```bash
# 1. Test data provider
python -c "import asyncio; from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider; print(asyncio.run(MarketDataProvider().check_connection()))"

# 2. Test pattern detection
python -c "from aiv3.core.consolidation_tracker import ConsolidationTracker; print('Pattern detection ready')"

# 3. Test backend
curl http://localhost:8000/health

# 4. Test frontend
curl http://localhost:3000
```

## 🎯 Quick Start Commands

```bash
# Minimal setup to see it working:
git clone https://github.com/RvL13Capital/stockgpt-paper-trade.git
cd stockgpt-paper-trade
pip install yfinance pandas numpy
python test_real_data.py

# Full system:
pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --reload &
cd ../frontend && npm install && npm start
```

## 📱 What You'll See

1. **Backend API** (http://localhost:8000/docs):
   - Interactive API documentation
   - Test endpoints directly
   - Authentication system

2. **Frontend** (http://localhost:3000):
   - Dashboard with real stock prices
   - Signal generation interface
   - Portfolio tracking
   - Backtesting tools

3. **Real Data Examples**:
   - Live market prices
   - Technical indicators
   - Pattern detection
   - Trading signals

## 🚀 Production Deployment

For production deployment, see:
- `DEPLOYMENT.md` - General deployment guide
- `FREE_DEPLOYMENT_GUIDE.md` - Deploy for free
- `DEPLOY_RENDER_SECURE.md` - Deploy on Render

## 💡 Tips

1. **Start Simple**: Run `test_real_data.py` first
2. **No Mock Data**: Everything uses real market data
3. **Free Data**: Works without paid API keys (uses Yahoo Finance)
4. **Cache Enabled**: Data is cached to reduce API calls
5. **Async Operations**: Most operations are async for better performance

Need help? Check the error messages - they usually tell you exactly what's missing!