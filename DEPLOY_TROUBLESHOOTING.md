# 🔧 Deployment Troubleshooting Guide

Common issues and solutions for deploying StockGPT online.

---

## ❌ Build Failures

### Issue: "scikit-learn compilation error" or "Cython error"

**Problem:** Python 3.13 doesn't have pre-built wheels for scikit-learn 1.3.2

**Solution:**
1. Use Python 3.11 (recommended)
2. Add `runtime.txt` file:
   ```
   python-3.11.7
   ```
3. Use `requirements-web.txt` instead of `requirements.txt`

**For Render.com:**
- The `render.yaml` now specifies Python 3.11.7
- Uses lightweight `requirements-web.txt`
- This avoids compilation issues

---

### Issue: "Build timeout" or "Out of memory"

**Problem:** Too many heavy dependencies

**Solution:**
Use the lightweight requirements file:
```bash
pip install -r requirements-web.txt
```

This excludes:
- FastAPI (not needed for Streamlit)
- PostgreSQL/SQLAlchemy (not needed)
- Redis (not needed)
- Heavy testing frameworks

---

### Issue: "Module not found" errors

**Problem:** Missing dependencies

**Solution:**
1. Check that `requirements-web.txt` includes the module
2. Add to `requirements-web.txt`:
   ```
   missing-package==version
   ```
3. Rebuild/redeploy

---

## 🚨 Runtime Errors

### Issue: "Port already in use"

**Problem:** Wrong port configuration

**Solution:**
For Render, use environment variable:
```python
import os
port = int(os.environ.get("PORT", 8501))
```

Update start command:
```bash
streamlit run streamlit_app.py --server.port $PORT
```

---

### Issue: "API key not found"

**Problem:** Environment variables not set

**Solution:**

**Streamlit Cloud:**
1. Go to app settings
2. Secrets section
3. Add:
   ```toml
   TWELVEDATA_API_KEY = "your_key"
   ALPHA_VANTAGE_API_KEY = "your_key"
   FMP_API_KEY = "your_key"
   FINNHUB_API_KEY = "your_key"
   ```

**Render:**
1. Dashboard → Environment
2. Add each key separately

**Railway:**
1. Variables tab
2. Add key-value pairs

---

### Issue: "Rate limit exceeded"

**Problem:** Too many API calls

**Solution:**
1. Streamlit caches data with `@st.cache_data`
2. Increase TTL (time-to-live):
   ```python
   @st.cache_data(ttl=1800)  # 30 minutes
   ```
3. Use session state to persist data

---

## 🐌 Performance Issues

### Issue: "App is slow"

**Solutions:**
1. **Enable caching:**
   ```python
   @st.cache_data(ttl=900)
   def fetch_data(symbol):
       ...
   ```

2. **Use session state:**
   ```python
   if 'data' not in st.session_state:
       st.session_state.data = fetch_data()
   ```

3. **Limit data fetching:**
   - Use smaller timeframes
   - Fetch fewer symbols
   - Reduce API calls

4. **Optimize imports:**
   - Import only when needed
   - Use lazy loading

---

## 🔍 Platform-Specific Issues

### Streamlit Cloud

**Issue: "App not updating"**
- Clear cache in Streamlit Cloud
- Reboot app from dashboard
- Check GitHub sync

**Issue: "Resources exceeded"**
- Streamlit Cloud has memory limits
- Use `requirements-web.txt` (lighter)
- Optimize data processing

---

### Render.com

**Issue: "Build failed - disk space"**
```yaml
buildCommand: |
  pip install --upgrade pip --no-cache-dir &&
  pip install -r requirements-web.txt --no-cache-dir
```

**Issue: "Free instance spun down"**
- Render free tier spins down after 15 min inactivity
- First request takes ~30 seconds to spin up
- This is normal behavior

---

### Railway

**Issue: "Deployment failed"**
1. Check logs in Railway dashboard
2. Verify `Procfile` exists:
   ```
   web: streamlit run streamlit_app.py --server.port $PORT
   ```
3. Set environment variables

---

### Heroku

**Issue: "Application error"**
1. Check buildpack:
   ```bash
   heroku buildpacks:set heroku/python
   ```
2. Verify `Procfile` format
3. Check logs:
   ```bash
   heroku logs --tail
   ```

---

## 🛠️ Quick Fixes

### Force rebuild
```bash
# Remove cache and rebuild
git commit --allow-empty -m "Force rebuild"
git push
```

### Test locally first
```bash
# Always test before deploying
streamlit run streamlit_app.py --server.port 8501
```

### Check Python version
```bash
python --version
# Should be 3.11.x for best compatibility
```

### Minimal requirements test
```bash
# Test with minimal deps
pip install streamlit plotly pandas yfinance
streamlit run streamlit_app.py
```

---

## 📊 Recommended Configuration

### Python Version
```
python-3.11.7
```

### Requirements
Use `requirements-web.txt` for deployments

### Start Command
```bash
streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

### Build Command
```bash
pip install --upgrade pip --no-cache-dir &&
pip install -r requirements-web.txt --no-cache-dir
```

---

## ✅ Checklist Before Deploying

- [ ] Using Python 3.11.7
- [ ] Using `requirements-web.txt`
- [ ] API keys set in environment
- [ ] Tested locally
- [ ] Correct start command
- [ ] GitHub repo up to date
- [ ] No sensitive data in code

---

## 🆘 Still Having Issues?

1. **Check deployment logs** - Most errors are shown there
2. **Test locally** - If it doesn't work locally, it won't work deployed
3. **Use minimal requirements** - Start with `requirements-web.txt`
4. **Check platform status** - Sometimes platforms have outages
5. **Try different platform** - If Render fails, try Streamlit Cloud

---

## 📚 Platform Documentation

- [Streamlit Deployment](https://docs.streamlit.io/streamlit-community-cloud)
- [Render Troubleshooting](https://render.com/docs/troubleshooting-deploys)
- [Railway Guides](https://docs.railway.app/deploy/deployments)
- [Heroku Python](https://devcenter.heroku.com/articles/python-support)

---

**Pro Tip:** Always test with `requirements-web.txt` locally before deploying to ensure all dependencies are correct!