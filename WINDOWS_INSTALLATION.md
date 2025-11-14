# StockGPT Windows Installation Guide

## 🪟 One-Click Windows Deployment

Deploy StockGPT Paper Trade Terminal on Windows with just a few clicks! This guide provides everything you need to get started quickly and easily.

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB minimum, 16GB recommended
- **CPU**: 4 cores minimum, 8 cores recommended
- **Storage**: 20GB free space minimum
- **Network**: Internet connection for downloads

### Software Prerequisites
- **Docker Desktop**: Latest version
- **PowerShell**: Version 5.1 or higher
- **Git**: Latest version (optional, for updates)

## 🚀 Quick Start (2-Minute Setup)

### Method 1: One-Click Installer (Recommended)

1. **Download StockGPT**
   ```powershell
   # Download the latest release
   # Or clone the repository
   git clone https://github.com/yourusername/stockgpt.git
   cd stockgpt
   ```

2. **Run One-Click Installer**
   - Double-click `StockGPT-Deploy.bat`
   - Choose your deployment option
   - Wait for installation to complete
   - Access StockGPT at `http://localhost`

### Method 2: PowerShell Deployment

1. **Open PowerShell as Administrator**
   - Right-click Start button
   - Select "Windows PowerShell (Admin)"

2. **Run Deployment Script**
   ```powershell
   # Navigate to StockGPT directory
   cd C:\path\to\stockgpt
   
   # Run deployment script
   .\windows-deploy.ps1
   ```

3. **Follow Interactive Prompts**
   - Choose deployment type
   - Wait for Docker installation (if needed)
   - Access StockGPT when complete

## 📦 Deployment Options

### 1. Development Mode (Quick Start)
Perfect for trying out StockGPT and development work.

```powershell
.\windows-deploy.ps1 -Development
```

**Features:**
- Hot reloading for development
- Detailed error messages
- Easy debugging access
- No SSL encryption

### 2. Production Mode (Full Deployment)
Complete production deployment with SSL and optimizations.

```powershell
.\windows-deploy.ps1 -Production
```

**Features:**
- SSL/TLS encryption
- Performance optimizations
- Security hardening
- Production-ready configuration

### 3. Production with Monitoring
Production deployment with full monitoring stack.

```powershell
.\windows-deploy.ps1 -Production -Monitoring
```

**Features:**
- Everything from Production mode
- Prometheus metrics
- Grafana dashboards
- Alert notifications
- Log aggregation

## 🔧 Management Commands

### Start StockGPT
```powershell
.\windows-deploy.ps1 -Development    # Quick development start
.\windows-deploy.ps1 -Production     # Production deployment
```

### Check Status
```powershell
.\windows-deploy.ps1 -Status
```

### View Logs
```powershell
.\windows-deploy.ps1 -Logs                    # All services
.\windows-deploy.ps1 -Logs backend            # Backend only
.\windows-deploy.ps1 -Logs frontend           # Frontend only
```

### Stop StockGPT
```powershell
.\windows-deploy.ps1 -Stop
```

### Restart StockGPT
```powershell
.\windows-deploy.ps1 -Restart
```

### Create Backup
```powershell
.\windows-deploy.ps1 -Backup
```

### Update StockGPT
```powershell
.\windows-deploy.ps1 -Update
```

## 📊 Access URLs

After successful deployment, access StockGPT at:

### Development Mode
- **Frontend**: http://localhost
- **API**: http://localhost/api
- **API Documentation**: http://localhost/api/docs

### Production Mode
- **Frontend**: https://localhost (with SSL)
- **API**: https://localhost/api
- **API Documentation**: https://localhost/api/docs

### With Monitoring
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

## 🛠️ Manual Installation (Alternative)

If you prefer manual installation or encounter issues with the automated script:

### 1. Install Docker Desktop

1. **Download Docker Desktop**
   - Visit https://docker.com/products/docker-desktop
   - Download for Windows
   - Run installer and follow prompts

2. **Configure Docker Desktop**
   - Start Docker Desktop
   - Enable WSL 2 integration (recommended)
   - Allocate at least 4GB RAM in settings
   - Restart Docker Desktop

### 2. Install Git (Optional)

1. **Download Git**
   - Visit https://git-scm.com/download/win
   - Download and run installer
   - Use default settings

### 3. Deploy StockGPT Manually

```powershell
# Clone repository
git clone https://github.com/yourusername/stockgpt.git
cd stockgpt

# Create environment file
Copy-Item .env.example .env

# Edit .env file with your configuration
notepad .env

# Deploy with Docker Compose
docker-compose up -d
```

## 🔐 SSL Certificate Setup

For production deployment with SSL:

### Automatic SSL Setup
```powershell
# Run SSL setup script
.\setup-ssl.sh
```

### Manual SSL Setup

1. **Generate Self-Signed Certificate**
   ```powershell
   # Using OpenSSL (if installed)
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
       -keyout ssl/privkey.pem `
       -out ssl/fullchain.pem `
       -subj "/C=US/ST=Local/L=Local/O=StockGPT/CN=localhost"
   ```

2. **Using PowerShell**
   ```powershell
   # Generate certificate with PowerShell
   $cert = New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation "cert:\LocalMachine\My"
   Export-PfxCertificate -Cert $cert -FilePath "ssl/localhost.pfx" -Password (ConvertTo-SecureString -String "password" -Force -AsPlainText)
   ```

## 🐛 Troubleshooting

### Common Issues

1. **Docker Not Starting**
   ```powershell
   # Check Docker status
   docker info
   
   # Restart Docker service
   Restart-Service docker
   ```

2. **Port Already in Use**
   ```powershell
   # Find process using port 80
   netstat -ano | findstr :80
   
   # Kill process (replace PID with actual process ID)
   taskkill /PID 1234 /F
   ```

3. **Memory Issues**
   ```powershell
   # Check memory usage
   Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10
   
   # Increase Docker memory allocation
   # Go to Docker Desktop Settings -> Resources -> Memory
   ```

4. **Permission Issues**
   ```powershell
   # Run as Administrator
   # Right-click PowerShell -> Run as Administrator
   ```

### Performance Optimization

1. **Increase Docker Memory**
   - Open Docker Desktop Settings
   - Go to Resources -> Memory
   - Increase to 8GB or more
   - Click Apply & Restart

2. **Optimize WSL 2**
   ```powershell
   # Create .wslconfig file
   notepad "$env:USERPROFILE\.wslconfig"
   
   # Add these lines:
   [wsl2]
   memory=8GB
   processors=4
   ```

3. **Disable Windows Defender for Docker**
   - Add Docker directories to Windows Defender exclusions
   - Include WSL 2 directories

## 📈 Performance Tuning

### Docker Desktop Settings
1. **Resources**
   - CPUs: 4 or more
   - Memory: 8GB or more
   - Disk: 20GB or more

2. **WSL 2 Integration**
   - Enable WSL 2 based engine
   - Add your Linux distribution

### Windows Optimizations
1. **Power Settings**
   - Set to "High Performance"
   - Disable sleep/hibernation during deployment

2. **Antivirus Exclusions**
   - Exclude Docker directories
   - Exclude StockGPT project directory

## 🔍 Monitoring and Debugging

### Check Service Health
```powershell
# Check all services
docker-compose ps

# Check specific service
docker-compose ps backend

# View service logs
docker-compose logs backend

# Follow logs in real-time
docker-compose logs -f backend
```

### Resource Monitoring
```powershell
# Check Docker resource usage
docker stats

# Check system resources
taskmgr
```

### Database Management
```powershell
# Connect to PostgreSQL
docker-compose exec postgres psql -U stockgpt_user -d stockgpt

# Backup database
docker-compose exec postgres pg_dump -U stockgpt_user stockgpt > backup.sql

# Restore database
docker-compose exec -T postgres psql -U stockgpt_user -d stockgpt < backup.sql
```

## 🔄 Updating StockGPT

### Automatic Update
```powershell
.\windows-deploy.ps1 -Update
```

### Manual Update
```powershell
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Clean up old images
docker image prune -f
```

## 🗄️ Backup and Recovery

### Create Backup
```powershell
.\windows-deploy.ps1 -Backup
```

### Manual Backup
```powershell
# Backup database
docker-compose exec postgres pg_dump -U stockgpt_user stockgpt > backup_$(Get-Date -Format 'yyyyMMdd').sql

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
Copy-Item redis_data\dump.rdb backup_redis.rdb

# Backup uploaded files
robocopy uploads backups\uploads /E
```

### Restore from Backup
```powershell
# Restore database
docker-compose exec -T postgres psql -U stockgpt_user -d stockgpt < backup.sql

# Restore Redis
docker-compose down
docker volume rm stockgpt_redis_data
Copy-Item backup_redis.rdb redis_data\dump.rdb
docker-compose up -d
```

## 🌐 Network Configuration

### Port Configuration
If you need to change default ports:

1. **Edit docker-compose.yml**
   ```yaml
   services:
     nginx:
       ports:
         - "8080:80"  # Change to port 8080
   ```

2. **Update .env file**
   ```
   FRONTEND_PORT=8080
   ```

### Firewall Configuration
```powershell
# Allow StockGPT ports
New-NetFirewallRule -DisplayName "StockGPT" -Direction Inbound -Protocol TCP -LocalPort 80,443,3000,8000,3001,9090 -Action Allow

# Check firewall rules
Get-NetFirewallRule -DisplayName "StockGPT"
```

## 📞 Support and Resources

### Getting Help
1. **Check Logs**: `docker-compose logs`
2. **Status Check**: `docker-compose ps`
3. **Documentation**: See README.md
4. **Community**: GitHub Issues

### Useful Commands
```powershell
# Quick status check
docker-compose ps

# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend

# Scale services
docker-compose up -d --scale backend=3

# Clean up
docker system prune -f
docker volume prune -f
```

## 🎉 Next Steps

After successful deployment:

1. **Access StockGPT**: Open http://localhost in your browser
2. **Create Account**: Register your first user account
3. **Create Portfolio**: Set up your first paper trading portfolio
4. **Explore Features**: Try AI signals, execute trades, use the journal
5. **Monitor Performance**: Check Grafana dashboards (if monitoring enabled)

## 📚 Additional Resources

- [Docker Desktop for Windows](https://docs.docker.com/docker-for-windows/)
- [PowerShell Documentation](https://docs.microsoft.com/en-us/powershell/)
- [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/)
- [StockGPT Documentation](README.md)

---

**🎉 Congratulations! You now have StockGPT running on Windows with one-click deployment!**

The platform is ready for paper trading, AI signal analysis, and trading education. Enjoy exploring all the features!