# StockGPT Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Docker Desktop

**Docker is required to run StockGPT.**

1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Run the installer (choose default settings)
3. **Restart your computer** after installation
4. Start Docker Desktop (wait for it to fully start - you'll see a green "running" status)

**Minimum System Requirements:**
- Windows 10/11 (64-bit)
- 8GB RAM (16GB recommended)
- 20GB free disk space

---

### Step 2: Deploy StockGPT

**Option A: Double-Click Deployment (Easiest)**
1. Double-click `DEPLOY.bat`
2. Wait for the deployment to complete
3. Access StockGPT at http://localhost

**Option B: PowerShell Deployment (More Control)**

Right-click PowerShell and select "Run as Administrator", then:

```powershell
# Navigate to StockGPT folder
cd "C:\Users\Pfenn\OneDrive\Desktop\RvL\OKComputer_StockGPT Phase 3(2)"

# Development mode (recommended for first-time setup)
.\deploy-simple.ps1 -Development

# OR Production mode (with SSL)
.\deploy-simple.ps1 -Production

# OR Production with monitoring
.\deploy-simple.ps1 -Production -Monitoring
```

---

### Step 3: Access StockGPT

Once deployment is complete, open your browser and go to:

- **Frontend:** http://localhost
- **API Documentation:** http://localhost/api/docs
- **Health Check:** http://localhost/api/health

---

## 📊 Management Commands

```powershell
# Check status
.\deploy-simple.ps1 -Status

# Stop all services
.\deploy-simple.ps1 -Stop

# View logs
docker-compose logs -f

# Restart services
.\deploy-simple.ps1 -Stop
.\deploy-simple.ps1 -Development
```

---

## ⚙️ Configuration (Optional)

### Update API Keys for Live Data

Edit the `.env` file (created after first deployment):

1. Open `.env` with Notepad:
   ```
   notepad .env
   ```

2. Replace these values with your actual API keys:
   - `FINNHUB_API_KEY=your_actual_key_here`
   - `ALPHA_VANTAGE_API_KEY=your_actual_key_here`

3. Restart StockGPT:
   ```powershell
   .\deploy-simple.ps1 -Stop
   .\deploy-simple.ps1 -Development
   ```

**Get Free API Keys:**
- Finnhub: https://finnhub.io/register
- Alpha Vantage: https://www.alphavantage.co/support/#api-key

---

## 🐛 Troubleshooting

### Docker Not Found
**Error:** "Docker is not installed!"

**Solution:**
1. Make sure Docker Desktop is installed
2. Start Docker Desktop application
3. Wait for Docker to fully start (green icon in system tray)
4. Try running the script again

### Port Already in Use
**Error:** "Port 80 is already in use"

**Solution:**
```powershell
# Find what's using port 80
netstat -ano | findstr :80

# Stop the conflicting service or change StockGPT port in docker-compose.yml
```

### Services Not Starting
**Solution:**
```powershell
# Check Docker is running
docker info

# View error logs
docker-compose logs

# Clean restart
docker-compose down
docker system prune -f
.\deploy-simple.ps1 -Development
```

### Out of Memory
**Solution:**
1. Open Docker Desktop
2. Go to Settings → Resources → Advanced
3. Increase Memory to at least 8GB
4. Click "Apply & Restart"

---

## 📁 Project Structure

```
OKComputer_StockGPT Phase 3(2)/
├── DEPLOY.bat              ← Double-click to deploy
├── deploy-simple.ps1       ← Main deployment script
├── docker-compose.yml      ← Docker configuration
├── backend/                ← API and ML models
├── frontend/               ← Web interface
├── .env                    ← Configuration (created on first run)
└── data/                   ← Database storage (created on first run)
```

---

## 🎯 Next Steps

After StockGPT is running:

1. **Create an Account:** Register at http://localhost
2. **Create a Portfolio:** Set up your first paper trading portfolio
3. **Get AI Signals:** Use the ML models to analyze stocks
4. **Execute Paper Trades:** Practice trading without real money
5. **Track Performance:** Monitor your trading performance

---

## 📞 Need Help?

- Check logs: `docker-compose logs -f`
- View status: `.\deploy-simple.ps1 -Status`
- See documentation: `README.md`
- GitHub Issues: [Report a problem](https://github.com/yourusername/stockgpt/issues)

---

**🎉 Enjoy using StockGPT!**
