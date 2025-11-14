#!/bin/bash

# StockGPT Deployment Script
set -e

echo "🚀 Starting StockGPT deployment..."

# Check if required environment variables are set
if [ -z "$FINNHUB_API_KEY" ]; then
    echo "❌ FINNHUB_API_KEY environment variable is not set"
    echo "Please set it using: export FINNHUB_API_KEY=your_api_key"
    exit 1
fi

if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    echo "❌ ALPHA_VANTAGE_API_KEY environment variable is not set"
    echo "Please set it using: export ALPHA_VANTAGE_API_KEY=your_api_key"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs data ssl

# Create environment file
echo "🔧 Creating environment file..."
cat > .env << EOF
# Database Configuration
POSTGRES_DB=stockgpt
POSTGRES_USER=stockgpt_user
POSTGRES_PASSWORD=stockgpt_password

# Redis Configuration
REDIS_PASSWORD=stockgpt_redis_password

# API Keys
FINNHUB_API_KEY=${FINNHUB_API_KEY}
ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}

# JWT Secret (Change this in production)
JWT_SECRET_KEY=your-secret-key-change-in-production-$(date +%s)

# Environment
ENVIRONMENT=production
DEBUG=false
EOF

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec backend alembic upgrade head

# Create superuser (optional)
echo "👤 Would you like to create a superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    docker-compose exec backend python -c "
from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import uuid

db = SessionLocal()
email = input('Enter email: ')
password = input('Enter password: ')
user = User(
    id=uuid.uuid4(),
    email=email,
    hashed_password=get_password_hash(password),
    is_active=True,
    is_superuser=True
)
db.add(user)
db.commit()
db.close()
print('Superuser created successfully!')
"
fi

echo "✅ StockGPT deployment completed successfully!"
echo "🌐 Frontend: http://localhost"
echo "🔧 API: http://localhost/api"
echo "📊 API Docs: http://localhost/api/docs"