# 🚀 Railway Deployment Guide - Backend Only

## 📋 Prerequisites
- Railway account (free tier available)
- MongoDB Atlas database (already configured)

## 🎯 Step-by-Step Deployment Instructions

### Step 1: Prepare Backend Directory
Your backend directory should have this structure:
```
backend/
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── Procfile                   # Railway startup command
├── runtime.txt               # Python version
├── railway.json              # Railway configuration
├── config.py                 # Configuration settings
├── database.py               # Database connection
├── models.py                 # Data models
├── auth.py                   # Authentication
├── schemas.py                # Pydantic schemas
└── .env                      # Environment variables (local only)
```

### Step 2: Set Up Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Create a new project

### Step 3: Upload Backend Directory
**Option A: Direct Upload**
1. In Railway dashboard, click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. **Important**: Set the root directory to `backend/`
   - In Railway settings, set "Root Directory" to `backend`

**Option B: Manual Upload**
1. Zip the backend folder
2. Upload the zip file to Railway
3. Railway will extract and deploy

### Step 4: Configure Environment Variables
In Railway dashboard, go to your project → Variables tab and add:

```
MONGODB_URL=mongodb+srv://gpsapp:upB19T8wF8YoDYqj@cluster0.wzw...
MONGODB_DATABASE=rideshare
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-change-this
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### Step 5: Deploy
1. Railway will automatically detect the Python project
2. It will install dependencies from `requirements.txt`
3. It will start the server using the `Procfile`
4. Wait for deployment to complete (usually 2-3 minutes)

### Step 6: Verify Deployment
1. Check the deployment logs in Railway dashboard
2. Visit your Railway URL: `https://your-app-name.railway.app`
3. Test the health endpoint: `https://your-app-name.railway.app/health`
4. Test the mobile endpoint: `https://your-app-name.railway.app/mobile-test`

## 🔧 Configuration Files Explained

### Procfile
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.5.0
pymongo==4.7.2
# ... other dependencies
```

### runtime.txt
```
python-3.11.0
```

### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 🚨 Troubleshooting

### Common Issues:

1. **ModuleNotFoundError: No module named 'backend'**
   - Solution: This won't happen since we're deploying from backend directory
   - All imports are relative to the backend directory

2. **MongoDB Connection Error**
   - Solution: Verify `MONGODB_URL` in Railway environment variables
   - Check MongoDB Atlas network access settings

3. **Port Binding Error**
   - Solution: Ensure `uvicorn` uses `0.0.0.0` host and `$PORT` environment variable

4. **Dependency Installation Failed**
   - Solution: Check `requirements.txt` for version conflicts
   - Ensure all dependencies are compatible

### Debug Commands:
```bash
# Test locally before deployment
cd backend
python -c "from main import app; print('✅ Import successful')"

# Test uvicorn startup
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📱 Update Mobile App Configuration

After successful deployment, update your mobile app's API configuration:

```typescript
// config/api.ts
export const API_BASE_URL = 'https://your-app-name.railway.app';
```

## 🔄 Continuous Deployment

Railway automatically redeploys when you push to your main branch. To deploy:

1. Make changes to your backend code
2. Commit and push to GitHub
3. Railway will automatically deploy the changes

## 📊 Monitoring

- **Logs**: View real-time logs in Railway dashboard
- **Metrics**: Monitor CPU, memory, and network usage
- **Health Checks**: Automatic health checks at `/health` endpoint

## 🎉 Success Indicators

Your deployment is successful when:
- ✅ Railway shows "Deployment successful"
- ✅ Health check passes: `GET /health` returns 200
- ✅ Mobile test passes: `GET /mobile-test` returns 200
- ✅ API docs accessible: `GET /docs` shows FastAPI docs

## 🔗 Useful URLs

After deployment, your app will be available at:
- **Main API**: `https://your-app-name.railway.app`
- **Health Check**: `https://your-app-name.railway.app/health`
- **API Docs**: `https://your-app-name.railway.app/docs`
- **Mobile Test**: `https://your-app-name.railway.app/mobile-test`

## 🆘 Support

If you encounter issues:
1. Check Railway deployment logs
2. Verify environment variables
3. Test endpoints manually
4. Check MongoDB Atlas connection
5. Review this guide for common solutions 