#!/bin/bash

# SSL Certificate Setup Script for StockGPT
set -e

echo "🔒 Setting up SSL certificates for StockGPT..."

# Create SSL directory
mkdir -p ssl
mkdir -p secrets

# Generate self-signed certificate for development/testing
echo "📝 Generating self-signed SSL certificate..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/privkey.pem \
    -out ssl/fullchain.pem \
    -subj "/C=US/ST=State/L=City/O=StockGPT/CN=localhost"

echo "✅ Self-signed certificate generated for localhost"

# Set proper permissions
chmod 600 ssl/privkey.pem
chmod 644 ssl/fullchain.pem

echo "🔐 Certificate permissions set correctly"

# Generate PostgreSQL password for production
if [ ! -f secrets/postgres_password.txt ]; then
    echo "🗄️  Generating PostgreSQL password..."
    openssl rand -base64 32 > secrets/postgres_password.txt
    chmod 600 secrets/postgres_password.txt
    echo "✅ PostgreSQL password generated"
fi

# Generate JWT secret for production
if [ ! -f secrets/jwt_secret.txt ]; then
    echo "🔑 Generating JWT secret..."
    openssl rand -base64 32 > secrets/jwt_secret.txt
    chmod 600 secrets/jwt_secret.txt
    echo "✅ JWT secret generated"
fi

# Create production environment file
if [ ! -f .env.prod ]; then
    echo "⚙️  Creating production environment file..."
    cat > .env.prod << EOF
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration
POSTGRES_DB=stockgpt_prod
POSTGRES_USER=stockgpt_prod_user
POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password

# Redis Configuration
REDIS_PASSWORD=$(openssl rand -base64 32)

# Security
JWT_SECRET_FILE=/run/secrets/jwt_secret
ACCESS_TOKEN_EXPIRE_MINUTES=60

# API Keys (replace with your actual keys)
FINNHUB_API_KEY=your_finnhub_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST=20
EOF
    echo "✅ Production environment file created"
fi

echo ""
echo "🎯 SSL Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. For production, replace the self-signed certificate with a proper SSL certificate"
echo "2. Update the domain name in nginx.prod.conf and .env.prod"
echo "3. Set your actual API keys in .env.prod"
echo "4. Deploy with: docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""
echo "🔐 Certificate Details:"
echo "- Private Key: ssl/privkey.pem"
echo "- Certificate: ssl/fullchain.pem"
echo "- PostgreSQL Password: secrets/postgres_password.txt"
echo "- JWT Secret: secrets/jwt_secret.txt"
echo ""
echo "⚠️  Security Notes:"
echo "- Keep the ssl and secrets directories secure"
echo "- Never commit these files to version control"
echo "- Use proper SSL certificates for production"
echo "- Regularly rotate secrets and certificates"