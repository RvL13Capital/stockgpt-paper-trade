# StockGPT Paper Trade Terminal

An AI-powered stock analysis and paper trading platform with advanced machine learning capabilities, real-time data processing, and comprehensive portfolio management.

## 🚀 Features

### Core Features
- **AI-Powered Trading Signals**: Advanced ML models using XGBoost and technical analysis
- **Paper Trading Engine**: Realistic trade execution with market simulation
- **Portfolio Management**: Multi-portfolio support with performance tracking
- **Real-time Market Data**: Live streaming from multiple data providers
- **Backtesting Framework**: Strategy testing with comprehensive metrics
- **Trading Journal**: AI-assisted trade analysis and improvement suggestions
- **Advanced Analytics**: Risk metrics, performance analysis, and insights

### Technical Highlights
- **Modern Architecture**: FastAPI backend with React frontend
- **Dark Theme UI**: Professional trading interface optimized for long sessions
- **Real-time Updates**: WebSocket connections for live data streaming
- **Comprehensive Testing**: Unit, integration, and performance tests
- **Docker Support**: Complete containerization with Docker Compose
- **Monitoring & Health Checks**: Built-in system monitoring and metrics

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database with optimized schemas
- **Redis**: Caching and session management
- **SQLAlchemy**: Async ORM for database operations
- **XGBoost**: Machine learning for signal generation
- **TA-Lib**: Technical analysis indicators
- **Celery**: Background task processing

### Frontend
- **React 18**: Modern React with concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first styling
- **Radix UI**: Accessible UI components
- **Recharts**: Interactive data visualization

### Infrastructure
- **Docker & Docker Compose**: Container orchestration
- **Nginx**: Reverse proxy and load balancing
- **PostgreSQL**: Database with replication support
- **Redis**: High-performance caching

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- API keys for:
  - Finnhub (free tier available)
  - Alpha Vantage (free tier available)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stockgpt-paper-trade-terminal
   ```

2. **Set up environment variables**
   ```bash
   export FINNHUB_API_KEY="your-finnhub-api-key"
   export ALPHA_VANTAGE_API_KEY="your-alpha-vantage-api-key"
   ```

3. **Deploy with Docker Compose**
   ```bash
   ./deploy.sh
   ```

4. **Access the application**
   - Frontend: http://localhost
   - API Documentation: http://localhost/api/docs
   - Health Check: http://localhost/api/health

### Manual Installation

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📊 Usage

### Getting Started

1. **Create an Account**: Register with your email and password
2. **Create a Portfolio**: Set up your first paper trading portfolio
3. **Explore AI Signals**: Check AI-generated trading signals for various stocks
4. **Execute Trades**: Place paper trades based on signals or your analysis
5. **Monitor Performance**: Track your portfolio performance and metrics
6. **Journal Your Trades**: Document your trading decisions and learnings

### Key Workflows

#### AI Signal Generation
```python
# Get AI signal for a stock
GET /api/v1/signals/AAPL

# Get signal explanation with SHAP values
GET /api/v1/signals/AAPL/explain

# Get bulk signals for multiple stocks
POST /api/v1/signals/bulk
{"symbols": ["AAPL", "GOOGL", "MSFT"]}
```

#### Portfolio Management
```python
# Create portfolio
POST /api/v1/portfolios
{
  "name": "My Trading Portfolio",
  "initial_capital": 100000.0
}

# Execute trade
POST /api/v1/trades
{
  "portfolio_id": "uuid",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 10,
  "order_type": "market"
}
```

#### Backtesting
```python
# Create backtest
POST /api/v1/backtests
{
  "name": "MA Strategy Test",
  "strategy_type": "moving_average",
  "symbols": ["AAPL"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-01"
}

# Run backtest
POST /api/v1/backtests/{id}/run
```

## 🧪 Testing

### Run All Tests
```bash
./test.sh
```

### Specific Test Categories
```bash
# Backend unit tests
docker-compose exec backend pytest tests/ -v

# Integration tests
python -m pytest integration_tests/ -v

# Performance tests
python -m pytest performance_tests/ -v
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Load and response time testing
- **Security Tests**: Authentication and authorization testing

## 📈 Monitoring & Observability

### Health Checks
- **Simple Health**: `GET /health`
- **Detailed Health**: `GET /api/v1/health/health`
- **Metrics**: `GET /api/v1/health/metrics`

### Key Metrics
- API response times
- Database query performance
- Redis memory usage
- System resource utilization
- Trading performance metrics

### Logging
- Structured JSON logging
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging
- Error tracking and alerting

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
FINNHUB_API_KEY=your-finnhub-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key

# Security
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Features
FEATURE_REAL_TIME_DATA=true
FEATURE_ADVANCED_CHARTS=true
FEATURE_MODEL_INSIGHTS=true
```

### Docker Compose Services
- **postgres**: PostgreSQL database
- **redis**: Redis cache and session store
- **backend**: FastAPI application
- **frontend**: React application
- **nginx**: Reverse proxy

## 🚀 Deployment

### Production Deployment
```bash
# Set production environment
export ENVIRONMENT=production
export DEBUG=false

# Deploy with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scaling Considerations
- **Database**: Use connection pooling and read replicas
- **Redis**: Cluster mode for high availability
- **Backend**: Horizontal scaling with load balancing
- **Frontend**: CDN for static assets

## 📚 API Documentation

### Interactive Documentation
- Swagger UI: http://localhost/api/docs
- ReDoc: http://localhost/api/redoc

### Key Endpoints
- **Authentication**: `/api/v1/auth/*`
- **Portfolio**: `/api/v1/portfolio/*`
- **Signals**: `/api/v1/signals/*`
- **Stocks**: `/api/v1/stocks/*`
- **Backtests**: `/api/v1/backtests/*`

## 🔒 Security

### Authentication
- JWT-based authentication
- Secure password hashing (bcrypt)
- Token expiration and refresh
- Rate limiting and IP blocking

### Data Protection
- HTTPS/TLS encryption
- Database encryption at rest
- Secure API key management
- Input validation and sanitization

## 📈 Performance Optimization

### Backend Optimizations
- Database query optimization
- Redis caching strategies
- Async request handling
- Connection pooling
- Background task processing

### Frontend Optimizations
- Code splitting and lazy loading
- Image optimization
- CDN integration
- Service worker caching
- Virtual scrolling for large datasets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and API docs
- **Issues**: Report bugs and feature requests
- **Discussions**: Join community discussions
- **Email**: support@stockgpt.com

## 🙏 Acknowledgments

- **Finnhub**: Real-time market data provider
- **Alpha Vantage**: Historical data provider
- **FastAPI**: Modern web framework
- **React**: Frontend framework
- **XGBoost**: Machine learning library
- **TA-Lib**: Technical analysis library

---

**Built with ❤️ for the trading community**