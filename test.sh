#!/bin/bash

# StockGPT Testing Script
set -e

echo "🧪 Starting StockGPT testing..."

# Function to check if service is healthy
check_service_health() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "🔍 Checking $service health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null; then
            echo "✅ $service is healthy"
            return 0
        fi
        echo "⏳ Waiting for $service... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    echo "❌ $service is not healthy after $max_attempts attempts"
    return 1
}

# Check API health
check_service_health "Backend API" "http://localhost:8000/api/health"

# Check frontend
check_service_health "Frontend" "http://localhost:3000"

# Run backend tests
echo "🧪 Running backend tests..."
docker-compose exec backend pytest tests/ -v

# Run frontend tests
echo "🧪 Running frontend tests..."
docker-compose exec frontend npm test -- --watchAll=false

# Integration tests
echo "🔗 Running integration tests..."
python3 -m pytest integration_tests/ -v

# Performance tests
echo "⚡ Running performance tests..."
python3 -m pytest performance_tests/ -v

echo "✅ All tests completed successfully!"