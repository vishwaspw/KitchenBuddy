# KitchenBuddy Railway Deployment Guide

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✅ Project Cleaned Up for Railway!

Your project has been optimized for Railway deployment. Unnecessary files have been removed:
- ❌ Docker files (Dockerfile, docker-compose.yml)
- ❌ Heroku files (Procfile, runtime.txt)
- ❌ Other deployment guides
- ❌ Installation scripts
- ✅ Only Railway-essential files remain

## Step 1: Prepare Your Repository

1. **Your code is ready!** All unnecessary files have been removed
2. **Push to GitHub** if you haven't already:
   ```bash
   git add .
   git commit -m "Ready for Railway deployment"
   git push origin main
   ```

## Step 2: Deploy to Railway

1. **Go to [Railway.app](https://railway.app)**
2. **Sign up/Login** with your GitHub account
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your KitchenBuddy repository**
6. **Railway will automatically detect it's a Python app**

## Step 3: Configure Environment Variables

In your Railway project dashboard:

1. **Go to "Variables" tab**
2. **Add these environment variables:**

```
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
FLASK_ENV=production
OPENAI_API_KEY=your-openai-api-key-here
PORT=5000
```

## Step 4: Deploy and Initialize Database

1. **Railway will automatically deploy your app** using the `railway.json` configuration
2. **Once deployed, go to "Deployments" tab**
3. **Click on your deployment**
4. **Open the terminal/console**
5. **Run these commands:**

```bash
# Initialize the database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Populate with sample recipes
python populate_db.py
```

## Step 5: Access Your App

1. **Go to "Settings" tab**
2. **Copy your app URL** (something like `https://your-app-name.railway.app`)
3. **Your KitchenBuddy is now live!**

## Step 6: Test Voice Features

1. **Visit your app URL**
2. **Sign up/Login**
3. **Go to Voice-Only Mode**
4. **Allow microphone access**
5. **Test voice commands like:**
   - "Open recipe pasta carbonara"
   - "Next step"
   - "Start timer 5 minutes"

## What's Included in Your Cleaned Project:

### ✅ Core Application Files:
- `app.py` - Main Flask application
- `wsgi.py` - Production WSGI entry point
- `requirements.txt` - Railway-optimized dependencies
- `railway.json` - Railway deployment configuration

### ✅ Essential Directories:
- `voice_assistant/` - Voice processing modules
- `models/` - Database models
- `templates/` - HTML templates
- `static/` - CSS, JS, and assets
- `recipes/` - Sample recipe data

### ✅ Database & Data:
- `populate_db.py` - Database population script
- `instance/` - Database files (will be created)

## Troubleshooting

### If Voice Features Don't Work:
1. **Check browser console** for errors
2. **Ensure HTTPS is enabled** (Railway provides this automatically)
3. **Allow microphone permissions** in browser
4. **Try different browsers** (Chrome works best)

### If Database Issues:
1. **Re-run database initialization commands**
2. **Check Railway logs** for errors
3. **Ensure all environment variables are set**

### If OpenAI Features Don't Work:
1. **Verify your OpenAI API key is correct**
2. **Check your OpenAI account has credits**
3. **Look at Railway logs** for API errors

## Monitoring Your App

- **Railway Dashboard**: Monitor resource usage
- **Logs**: View real-time application logs
- **Metrics**: Track performance and errors

## Scaling Up

If you need more resources:
1. **Upgrade Railway plan** for more CPU/memory
2. **Add PostgreSQL** for better database performance
3. **Set up custom domain** for professional URL

## Cost

- **Free Tier**: Perfect for development and small-scale use
- **Paid Plans**: Start at $5/month for more resources

## 🎉 You're Ready to Deploy!

Your KitchenBuddy project is now perfectly optimized for Railway deployment. Just follow the steps above and your voice-controlled cooking assistant will be live on the web!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 