# StockGPT Backend API

FastAPI-based backend for the StockGPT Paper Trade Terminal, providing data ingestion, signal generation, portfolio management, and trading execution services.

## Features

- **Data Ingestion**: Automated EOD data fetching from Polygon.io and Tiingo
- **Technical Analysis**: Comprehensive indicator calculations (RSI, MACD, Bollinger Bands, etc.)
- **ML Signal Generation**: AI-powered trading signals with confidence scoring
- **Portfolio Management**: Real-time position tracking and P&L calculation
- **Paper Trading**: Simulated trade execution with realistic fees and slippage
- **Scheduled Tasks**: Automated data updates and signal generation
- **RESTful API**: Clean, documented API with FastAPI

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session management and caching
- **ML**: XGBoost for signal generation
- **Task Queue**: Celery for background tasks
- **Monitoring**: Prometheus metrics and structured logging

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API endpoints
│   ├── core/               # Core functionality (config, database, logging)
│   ├── models/             # SQLAlchemy models
│   ├── services/           # Business logic services
│   └── main.py             # FastAPI application
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Development environment
├── Dockerfile             # Container configuration
└── init.sql              # Database initialization
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Installation

1. **Clone and setup environment:**
```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup database:**
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head
```

4. **Run the application:**
```bash
uvicorn app.main:app --reload
```

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login with email and OTP
- `POST /api/v1/auth/request-otp` - Request OTP
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/verify-token` - Verify JWT token

### Stocks
- `GET /api/v1/stocks` - List stocks with filtering
- `GET /api/v1/stocks/{symbol}/prices` - Get historical prices
- `GET /api/v1/stocks/{symbol}/features` - Get technical indicators
- `GET /api/v1/stocks/{symbol}/latest` - Get latest price

### Signals
- `GET /api/v1/signals` - List trading signals
- `GET /api/v1/signals/{id}` - Get signal details
- `POST /api/v1/signals/{id}/action` - Take action on signal

### Portfolio
- `GET /api/v1/portfolio/summary` - Portfolio overview
- `GET /api/v1/portfolio/positions` - Current positions
- `GET /api/v1/portfolio/allocation` - Sector allocation
- `GET /api/v1/portfolio/performance` - Performance history

### Data Management
- `POST /api/v1/data/ingest/stocks` - Ingest stock data
- `GET /api/v1/data/symbols/available` - Get available symbols
- `POST /api/v1/data/ingest/scheduled` - Run scheduled ingestion

## Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/stockgpt_db
REDIS_URL=redis://localhost:6379

# External APIs
POLYGON_API_KEY=your_polygon_api_key
TIINGO_API_KEY=your_tiingo_api_key

# Email (for OTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your_secret_key_for_jwt

# Feature Flags
FEATURE_REAL_TIME_DATA=true
FEATURE_ADVANCED_CHARTS=true
FEATURE_MODEL_INSIGHTS=true
```

## Services

### Data Ingestion Service
- **Purpose**: Fetch and process EOD stock data
- **Schedule**: Daily at 22:00 UTC (after market close)
- **Sources**: Polygon.io, Tiingo
- **Processing**: Technical indicator calculation, feature engineering

### Signal Engine Service
- **Purpose**: Generate AI-powered trading signals
- **Schedule**: Hourly during market hours
- **Model**: XGBoost classifier with technical features
- **Output**: Buy/Sell/Hold signals with confidence scores

### Trade Engine Service
- **Purpose**: Execute paper trades based on signals
- **Features**: Position sizing, risk management, P&L tracking
- **Execution**: Simulated market orders with realistic fees
- **Portfolio**: Real-time valuation and performance metrics

### Scheduler Service
- **Purpose**: Manage automated background tasks
- **Tasks**:
  - Daily data ingestion (22:00 UTC)
  - Hourly signal generation (market hours)
  - Portfolio updates (every 15 minutes)
  - OTP reset (daily at 00:00 UTC)

## Data Models

### Stock Data
- **Stock**: Company information and metadata
- **StockPrice**: OHLCV data with adjustments
- **StockFeature**: Technical indicators and features

### Trading Data
- **Signal**: AI-generated trading signals
- **Portfolio**: User portfolio information
- **Position**: Open positions tracking
- **Trade**: Executed trades history

### User Data
- **User**: User accounts and preferences
- **ModelPerformance**: ML model performance tracking

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Format code
black app/
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

## Production Deployment

### Using Docker
```bash
# Build and start
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Monitoring
- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus metrics at `/metrics`
- **Logging**: Structured JSON logs
- **Performance**: Database query optimization

## API Documentation

When running the application, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Security

- **Authentication**: JWT tokens with OTP-based login
- **Authorization**: Role-based access control
- **Rate Limiting**: API rate limiting per user
- **Input Validation**: Pydantic models with strict validation
- **SQL Injection**: Protected by SQLAlchemy ORM
- **CORS**: Configured for specific origins

## Performance

- **Database**: Connection pooling, query optimization
- **Caching**: Redis for session management
- **Async**: Full async/await implementation
- **Background Tasks**: Celery for heavy processing
- **CDN**: Static file serving optimization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes quality checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or support, please open an issue in the repository or contact the development team.