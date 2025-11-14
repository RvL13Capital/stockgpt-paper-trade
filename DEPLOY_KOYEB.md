# Deploy StockGPT to Koyeb (Free Tier)

## Prerequisites
- GitHub account
- Koyeb account (free tier - no credit card required for trial)

## Step 1: Push Code to GitHub

1. Create a new repository on GitHub:
   - Go to https://github.com/new
   - Name: `stockgpt-paper-trade`
   - Keep it Private
   - Don't initialize with README (we already have one)
   - Click "Create repository"

2. Push your code:
   ```bash
   git add .
   git commit -m "Initial commit - StockGPT Paper Trading Terminal"
   git remote add origin https://github.com/YOUR_USERNAME/stockgpt-paper-trade.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Sign Up for Koyeb

1. Go to https://www.koyeb.com/
2. Click "Sign Up" and use GitHub login
3. Verify your email

## Step 3: Create PostgreSQL Database

1. In Koyeb dashboard, click "Create Service"
2. Select "Database"
3. Choose "PostgreSQL"
4. Select "Free tier"
5. Name: `stockgpt-db`
6. Click "Create Database"
7. Wait for it to be ready (2-3 minutes)
8. Copy the DATABASE_URL (you'll need this)

## Step 4: Create Redis Database

1. Click "Create Service" again
2. Select "Database"
3. Choose "Redis"
4. Select "Free tier"
5. Name: `stockgpt-redis`
6. Click "Create Database"
7. Wait for it to be ready
8. Copy the REDIS_URL

## Step 5: Deploy Backend

1. Click "Create Service" → "Web Service"
2. Select "GitHub" and connect your repository
3. Choose your `stockgpt-paper-trade` repository
4. Configure:
   - **Name**: `stockgpt-backend`
   - **Build method**: Dockerfile
   - **Dockerfile path**: `backend/Dockerfile`
   - **Port**: 8000

5. Add Environment Variables:
   ```
   DATABASE_URL=<paste from Step 3>
   REDIS_URL=<paste from Step 4>
   ALPHA_VANTAGE_API_KEY=FPG7DCR33BFK2HDP
   FINNHUB_API_KEY=d2f75n1r01qj3egrhu7gd2f75n1r01qj3egrhu80
   TWELVEDATA_API_KEY=5361b6392f4941d99f08d14d22551cb2
   FMP_API_KEY=smkqs1APQJVN2JuJAxSDkEvk7tDdTdZm
   JWT_SECRET_KEY=your-super-secret-key-here-change-this
   ENVIRONMENT=production
   DEBUG=false
   ```

6. Click "Deploy"
7. Wait 5-10 minutes for build and deployment
8. Copy the backend URL (e.g., `stockgpt-backend-xyz.koyeb.app`)

## Step 6: Deploy Frontend

1. Click "Create Service" → "Web Service"
2. Select your GitHub repository again
3. Configure:
   - **Name**: `stockgpt-frontend`
   - **Build method**: Dockerfile
   - **Dockerfile path**: `frontend/Dockerfile.prod`
   - **Port**: 80

4. Add Environment Variables:
   ```
   VITE_API_URL=https://stockgpt-backend-xyz.koyeb.app/api
   VITE_WS_URL=wss://stockgpt-backend-xyz.koyeb.app/ws
   VITE_MOCK_DATA=false
   VITE_DEBUG_MODE=false
   VITE_AUTH_ENABLED=true
   ```
   (Replace `stockgpt-backend-xyz.koyeb.app` with your actual backend URL from Step 5)

5. Click "Deploy"
6. Wait 5-10 minutes

## Step 7: Access Your App

Your app will be available at:
`https://stockgpt-frontend-xyz.koyeb.app`

## Monitoring

- Check logs in Koyeb dashboard
- Monitor database usage
- Free tier includes:
  - 2 web services
  - 2 databases
  - $5.50 credits/month (enough for light usage)

## Troubleshooting

### Build Fails
- Check Dockerfile paths are correct
- Verify environment variables are set
- Check build logs in Koyeb dashboard

### Backend Won't Start
- Verify DATABASE_URL and REDIS_URL are correct
- Check that database services are running
- Review backend logs

### Frontend Can't Connect
- Verify VITE_API_URL matches your backend URL
- Check CORS settings
- Ensure backend is running

## Cost Monitoring

Free tier limits:
- If you exceed $5.50/month, you'll need to upgrade
- Monitor usage in Koyeb dashboard
- Can always pause services when not in use

## Notes

- First deploy takes 10-15 minutes
- Subsequent deploys (on git push) are automatic
- Free tier is enough for development and testing
- Can upgrade to paid tier for production use
