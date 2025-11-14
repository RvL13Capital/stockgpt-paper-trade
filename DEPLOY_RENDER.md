# Deploy StockGPT to Render (Free Tier)

## Why Render?

- **Free tier**: Generous free allowance
- **PostgreSQL**: Free database included
- **Redis**: Free tier available
- **Auto-deploy**: Updates automatically on git push
- **Easy setup**: 20-30 minutes total
- **No credit card required** for free tier

---

## Step-by-Step Deployment Guide

### Step 1: Sign Up for Render

1. Go to https://render.com/
2. Click **"Get Started"** or **"Sign Up"**
3. Choose **"Sign in with GitHub"** (recommended - easier setup)
4. Authorize Render to access your GitHub repositories
5. You'll be taken to your Render dashboard

---

### Step 2: Create PostgreSQL Database

1. In Render dashboard, click **"New +"** (top right)
2. Select **"PostgreSQL"**
3. Configuration:
   - **Name**: `stockgpt-db`
   - **Database**: `stockgpt` (will be created automatically)
   - **User**: `stockgpt_user` (or leave default)
   - **Region**: Choose closest to you (e.g., Oregon, Frankfurt)
   - **PostgreSQL Version**: 15 or 16 (latest)
   - **Instance Type**: **Free** (should be selected by default)

4. Click **"Create Database"**
5. Wait 2-3 minutes for provisioning
6. Once ready, click on the database name
7. Scroll down to **"Connections"** section
8. **Copy the "Internal Database URL"** (starts with `postgresql://`)
   - Save this - you'll need it later
   - Example: `postgresql://stockgpt_user:password@dpg-xxx.oregon-postgres.render.com/stockgpt`

---

### Step 3: Create Redis Instance

1. Click **"New +"** again
2. Select **"Redis"**
3. Configuration:
   - **Name**: `stockgpt-redis`
   - **Region**: Same as PostgreSQL
   - **Instance Type**: **Free**

4. Click **"Create Redis"**
5. Wait 2-3 minutes
6. Once ready, click on the Redis instance
7. **Copy the "Internal Redis URL"** (starts with `redis://`)
   - Save this with your PostgreSQL URL
   - Example: `redis://red-xxx.oregon-redis.render.com:6379`

---

### Step 4: Deploy Backend Service

1. Click **"New +"** → **"Web Service"**
2. Choose **"Build and deploy from a Git repository"**
3. Click **"Connect account"** if needed, then select your repository:
   - **Repository**: `RvL13Capital/stockgpt-paper-trade`
4. Click **"Connect"**

5. **Configure the service**:
   - **Name**: `stockgpt-backend`
   - **Region**: Same as databases (important!)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: **Docker**
   - **Instance Type**: **Free**

6. **Add Environment Variables** (click "Add Environment Variable"):

   Click **"Add from .env"** and paste all at once:
   ```
   DATABASE_URL=<paste your Internal Database URL from Step 2>
   REDIS_URL=<paste your Internal Redis URL from Step 3>
   ALPHA_VANTAGE_API_KEY=FPG7DCR33BFK2HDP
   FINNHUB_API_KEY=d2f75n1r01qj3egrhu7gd2f75n1r01qj3egrhu80
   TWELVEDATA_API_KEY=5361b6392f4941d99f08d14d22551cb2
   FMP_API_KEY=smkqs1APQJVN2JuJAxSDkEvk7tDdTdZm
   JWT_SECRET_KEY=change-this-to-a-super-secret-random-key-min-32-chars
   ENVIRONMENT=production
   DEBUG=false
   ```

7. **Scroll down** and click **"Create Web Service"**
8. Wait 5-10 minutes for the build to complete
9. Once deployed, you'll see **"Your service is live"**
10. **Copy your backend URL** (e.g., `stockgpt-backend.onrender.com`)
    - You'll need this for the frontend

---

### Step 5: Deploy Frontend Service

1. Click **"New +"** → **"Web Service"**
2. **"Build and deploy from a Git repository"**
3. Select your repository: `RvL13Capital/stockgpt-paper-trade`
4. Click **"Connect"**

5. **Configure the service**:
   - **Name**: `stockgpt-frontend`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Runtime**: **Docker**
   - **Instance Type**: **Free**

6. **Add Environment Variables**:

   Replace `<BACKEND-URL>` with your actual backend URL from Step 4:
   ```
   VITE_API_URL=https://<BACKEND-URL>/api
   VITE_WS_URL=wss://<BACKEND-URL>/ws
   VITE_MOCK_DATA=false
   VITE_DEBUG_MODE=false
   VITE_AUTH_ENABLED=true
   ```

   **Example** (if your backend is at `stockgpt-backend.onrender.com`):
   ```
   VITE_API_URL=https://stockgpt-backend.onrender.com/api
   VITE_WS_URL=wss://stockgpt-backend.onrender.com/ws
   VITE_MOCK_DATA=false
   VITE_DEBUG_MODE=false
   VITE_AUTH_ENABLED=true
   ```

7. Click **"Create Web Service"**
8. Wait 5-10 minutes for build
9. Once deployed, you'll see **"Your service is live"**

---

### Step 6: Access Your Application

Your StockGPT app is now live at:
**`https://stockgpt-frontend.onrender.com`**

(or whatever URL Render assigned to your frontend)

---

## Important Notes About Free Tier

### Limitations:
- **Services spin down after 15 minutes of inactivity**
- **First request after spin-down takes 50-60 seconds** to wake up
- Database and Redis stay active

### How to Work Around Spin-Down:
1. **UptimeRobot**: Set up free monitoring at https://uptimerobot.com/ to ping your app every 5 minutes
2. **Cron-job.org**: Free service to keep your app alive
3. **Upgrade to paid** ($7/month) for always-on service

---

## Monitoring and Logs

### View Logs:
1. Click on your service (backend or frontend)
2. Click **"Logs"** tab
3. See real-time logs

### Check Status:
- Green dot = Running
- Yellow dot = Deploying
- Red dot = Failed

---

## Updating Your App

Render automatically deploys when you push to GitHub:

```bash
cd "C:\Users\Pfenn\OneDrive\Desktop\RvL\OKComputer_StockGPT Phase 3(2)"
git add .
git commit -m "Update: describe your changes"
git push origin main
```

Render will automatically:
1. Detect the push
2. Build new Docker images
3. Deploy updated services
4. Zero-downtime deployment

---

## Troubleshooting

### Backend Won't Start
1. Check logs for errors
2. Verify DATABASE_URL and REDIS_URL are correct
3. Ensure all environment variables are set
4. Check that databases are running

### Frontend Can't Connect to Backend
1. Verify VITE_API_URL matches your backend URL exactly
2. Check backend is running (green dot)
3. Test backend directly: `https://your-backend.onrender.com/health`

### Database Connection Issues
1. Make sure you used **Internal Database URL** (not External)
2. Verify backend and database are in same region
3. Check database is running

### Build Fails
1. Check build logs for specific error
2. Verify Dockerfile paths are correct
3. Check that `Root Directory` is set correctly

---

## Cost Breakdown (Free Tier)

| Service | Free Tier |
|---------|-----------|
| Web Services (2) | 750 hours/month total |
| PostgreSQL | 90 days free, then expires |
| Redis | 25 MB, persists for 90 days |

**Note**: After 90 days, you'll need to upgrade to paid ($7/month for PostgreSQL, $1/month for Redis) or migrate to another service.

---

## Next Steps After Deployment

1. **Test the application**: Register, create portfolio, check signals
2. **Set up monitoring**: UptimeRobot to prevent spin-down
3. **Monitor usage**: Check your dashboard for resource usage
4. **Consider upgrading**: If you use it heavily, $7/month removes spin-down

---

## Alternative: Upgrade Options

If you need better performance:
- **Starter Plan**: $7/month per service
  - No spin-down
  - 512 MB RAM
  - Always on
- **PostgreSQL**: $7/month
  - 1 GB storage
  - No expiration
- **Redis**: $1/month
  - 25 MB storage

---

**Your app will be live at:**
- Frontend: `https://stockgpt-frontend.onrender.com`
- Backend: `https://stockgpt-backend.onrender.com`
- API Docs: `https://stockgpt-backend.onrender.com/api/docs`

Good luck! 🚀
