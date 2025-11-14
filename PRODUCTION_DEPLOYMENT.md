# StockGPT Production Deployment Guide

## 🚀 Production Deployment Overview

This guide provides step-by-step instructions for deploying StockGPT Paper Trade Terminal in a production environment with SSL, monitoring, and high availability.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **CPU**: 4 cores minimum, 8 cores recommended
- **Storage**: 100GB SSD minimum
- **Network**: Static IP address, domain name

### Software Requirements
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: Latest version
- **OpenSSL**: For SSL certificate generation

### External Services
- **Domain Name**: Registered domain with DNS control
- **Email Service**: For alerts and notifications
- **API Keys**: Finnhub and Alpha Vantage accounts

## 🔐 Security Setup

### 1. SSL Certificate Setup

```bash
# Run the SSL setup script
./setup-ssl.sh
```

**For Production SSL:**
```bash
# Use Let's Encrypt (recommended)
sudo apt update
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to SSL directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chown $USER:$USER ssl/*
```

### 2. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 9090/tcp  # Prometheus (restrict to monitoring IPs)
sudo ufw allow 3001/tcp  # Grafana (restrict to monitoring IPs)

# Enable firewall
sudo ufw enable
```

### 3. Secrets Management

```bash
# Create secrets directory
mkdir -p secrets

# Generate secure passwords
openssl rand -base64 32 > secrets/postgres_password.txt
openssl rand -base64 32 > secrets/jwt_secret.txt
openssl rand -base64 32 > secrets/redis_password.txt

# Set proper permissions
chmod 600 secrets/*.txt
```

## 🚀 Production Deployment

### 1. Environment Configuration

```bash
# Copy and edit production environment file
cp .env.prod.example .env.prod

# Edit the file with your configuration
nano .env.prod
```

**Required Configuration:**
- Domain name
- API keys
- Email settings
- Database credentials

### 2. Deploy with Monitoring

```bash
# Deploy all services with monitoring
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d

# Check deployment status
docker-compose ps
```

### 3. Verify Deployment

```bash
# Run deployment verification
python3 verify_deployment.py

# Check service health
curl -f http://localhost/health
curl -f https://yourdomain.com/health
```

## 📊 Monitoring Setup

### 1. Access Monitoring Dashboards

- **Grafana**: https://yourdomain.com:3001 (admin/admin123)
- **Prometheus**: https://yourdomain.com:9090
- **AlertManager**: https://yourdomain.com:9093

### 2. Configure Alerts

```bash
# Edit alert configuration
nano monitoring/alertmanager.yml

# Update email settings and recipients
# Restart alertmanager
docker-compose restart alertmanager
```

### 3. Set Up Log Aggregation

```bash
# Access Loki logs
curl -G -s "http://localhost:3100/loki/api/v1/query" --data-urlencode 'query={job="stockgpt-backend"}' | jq
```

## 🔧 Production Optimizations

### 1. Database Optimization

```sql
-- Connect to PostgreSQL
docker-compose exec postgres psql -U stockgpt_prod_user -d stockgpt_prod

-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_portfolio_performance ON portfolios(user_id, created_at);
CREATE INDEX CONCURRENTLY idx_trade_portfolio_symbol ON trades(portfolio_id, symbol, created_at);
CREATE INDEX CONCURRENTLY idx_position_portfolio_symbol ON positions(portfolio_id, symbol, updated_at);

-- Enable query logging for slow queries
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

### 2. Redis Optimization

```bash
# Connect to Redis
docker-compose exec redis redis-cli -a $REDIS_PASSWORD

# Monitor Redis performance
redis-cli -a $REDIS_PASSWORD monitor

# Check memory usage
redis-cli -a $REDIS_PASSWORD info memory
```

### 3. Application Scaling

```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Configure load balancing in nginx.conf
# Update upstream backend configuration
```

## 🛡️ Security Hardening

### 1. Nginx Security

```nginx
# Add to nginx.prod.conf
server {
    # Hide nginx version
    server_tokens off;
    
    # Prevent clickjacking
    add_header X-Frame-Options DENY;
    
    # Prevent MIME type sniffing
    add_header X-Content-Type-Options nosniff;
    
    # Enable XSS protection
    add_header X-XSS-Protection "1; mode=block";
    
    # Force HTTPS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Content Security Policy
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:; media-src 'self'; object-src 'none'; child-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'";
}
```

### 2. Docker Security

```bash
# Run containers as non-root user
# Use read-only file systems where possible
# Limit container capabilities

# Example security options
docker run --security-opt no-new-privileges:true \
           --cap-drop ALL \
           --cap-add NET_BIND_SERVICE \
           --read-only \
           --tmpfs /tmp \
           your-image
```

### 3. Network Security

```bash
# Create isolated Docker networks
docker network create --driver bridge stockgpt_frontend
docker network create --driver bridge stockgpt_backend

# Apply network policies
docker-compose --network stockgpt_frontend up -d
```

## 📈 Performance Monitoring

### 1. Key Metrics to Monitor

**Application Metrics:**
- API response times
- Error rates
- Request throughput
- Database query performance
- Cache hit rates

**System Metrics:**
- CPU usage
- Memory utilization
- Disk I/O
- Network throughput
- Container resource usage

**Business Metrics:**
- User registrations
- Active sessions
- Trade execution times
- Signal generation accuracy

### 2. Performance Benchmarks

```bash
# Run performance tests
./test.sh

# Load testing with Apache Bench
ab -n 1000 -c 10 https://yourdomain.com/api/v1/portfolios

# Database performance testing
docker-compose exec postgres pgbench -i -s 10 stockgpt_prod
```

## 🔄 Backup and Recovery

### 1. Database Backups

```bash
# Automated backup script
cat > backup-database.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/stockgpt"
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker-compose exec postgres pg_dump -U stockgpt_prod_user stockgpt_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Database backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
EOF

chmod +x backup-database.sh

# Add to crontab for daily backups
0 2 * * * /path/to/backup-database.sh
```

### 2. Application Data Backup

```bash
# Backup Redis data
docker-compose exec redis redis-cli -a $REDIS_PASSWORD BGSAVE

# Backup uploaded files
tar -czf backup_files_$(date +%Y%m%d).tar.gz /path/to/uploaded/files/
```

### 3. Disaster Recovery

```bash
# Restore database
docker-compose exec postgres psql -U stockgpt_prod_user -d stockgpt_prod < db_backup.sql

# Restore Redis data
docker-compose exec redis redis-cli -a $REDIS_PASSWORD --rdb /data/dump.rdb
```

## 🔧 Maintenance

### 1. Regular Updates

```bash
# Update Docker images
docker-compose pull

# Update application code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 2. Log Management

```bash
# Configure log rotation
cat > monitoring/logrotate.conf << 'EOF'
/var/log/stockgpt/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

# Clean up Docker logs
docker system prune -f
docker volume prune -f
```

### 3. Certificate Renewal

```bash
# Let's Encrypt auto-renewal
sudo crontab -e

# Add line for automatic renewal
0 2 * * * /usr/bin/certbot renew --quiet --no-self-upgrade
```

## 🚨 Troubleshooting

### Common Issues

1. **SSL Certificate Issues**
   ```bash
   # Check certificate validity
   openssl x509 -in ssl/fullchain.pem -text -noout
   
   # Test SSL connection
   openssl s_client -connect yourdomain.com:443
   ```

2. **Database Connection Issues**
   ```bash
   # Check database connectivity
   docker-compose exec backend python -c "from app.database import engine; print(engine.connect())"
   
   # Check PostgreSQL logs
   docker-compose logs postgres
   ```

3. **Performance Issues**
   ```bash
   # Check system resources
   docker stats
   
   # Analyze slow queries
   docker-compose exec postgres psql -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   ```

### Emergency Procedures

1. **Immediate Rollback**
   ```bash
   # Rollback to previous version
   git checkout previous-stable-tag
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

2. **Database Recovery**
   ```bash
   # Restore from backup
   docker-compose down
   docker volume rm stockgpt_postgres_data
   ./backup-database.sh restore latest
   docker-compose up -d
   ```

## 📞 Support and Monitoring

### 1. Set Up Monitoring Alerts

- Configure email notifications in `alertmanager.yml`
- Set up Slack/Teams webhooks
- Configure PagerDuty integration

### 2. Health Checks

```bash
# Create health check script
cat > health-check.sh << 'EOF'
#!/bin/bash
# Check application health
curl -f https://yourdomain.com/health || exit 1

# Check database connectivity
docker-compose exec backend python -c "from app.database import engine; print('DB OK')"

# Check Redis connectivity
docker-compose exec redis redis-cli ping || exit 1

echo "All systems healthy"
EOF

chmod +x health-check.sh
```

### 3. Performance Monitoring

```bash
# Set up continuous monitoring
watch -n 60 './health-check.sh >> /var/log/health-check.log'
```

## 🎯 Post-Deployment Checklist

- [ ] SSL certificates configured and valid
- [ ] Domain name pointing to server IP
- [ ] Firewall configured with necessary ports
- [ ] Monitoring dashboards accessible
- [ ] Alert notifications configured
- [ ] Backup procedures in place
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Log aggregation working
- [ ] Performance benchmarks met
- [ ] Disaster recovery tested
- [ ] Documentation updated

## 📚 Additional Resources

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Nginx Security Headers](https://www.nginx.com/blog/http-security-headers/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Performance Optimization](https://redis.io/docs/manual/performance/)

## 🆘 Support

For production support:
- Email: support@stockgpt.com
- Slack: #stockgpt-support
- Emergency: +1-555-STOCKGPT

---

**🎉 Congratulations! Your StockGPT Paper Trade Terminal is now production-ready with enterprise-grade security, monitoring, and performance optimizations.**