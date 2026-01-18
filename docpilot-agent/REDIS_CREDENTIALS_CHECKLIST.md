# Hosted Redis - Quick Setup Checklist

## 📋 Things YOU NEED TO PROVIDE

### **Step 1: Choose a Redis Provider**
- [ ] Redis Cloud (https://redis.io/try-free) - **Recommended, Free tier**
- [ ] AWS ElastiCache
- [ ] Azure Cache for Redis
- [ ] Google Cloud Memorystore
- [ ] DigitalOcean Managed Redis
- [ ] Heroku Redis

### **Step 2: Create Redis Instance**
Follow your provider's instructions to create a new Redis database

### **Step 3: Collect These 3 Credentials**

From your Redis provider dashboard, copy:

1. **Redis Host/Endpoint**
   - Example: `redis-12345.c123.us-east-1-2.ec2.cloud.redis.io`
   - Copy from: `_____________________________`

2. **Redis Port** 
   - Usually: `6379` (standard) or `6380` (SSL)
   - Your port: `_____________________________`

3. **Redis Password/Auth Token**
   - Copy from: `_____________________________`
   - **Keep this SECRET!**

---

## 🔧 Update Your Configuration

### Edit `.env` file:

Replace this:
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

With this:
```env
CELERY_BROKER_URL=redis://:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/0
CELERY_RESULT_BACKEND=redis://:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/1
```

### Real Example (Redis Cloud):
```env
CELERY_BROKER_URL=redis://:user123secure456@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/0
CELERY_RESULT_BACKEND=redis://:user123secure456@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/1
```

---

## ✅ Verification

### Test 1: Check Configuration
```bash
myenv\Scripts\python -c "
from backend.core.config import settings
print('Broker URL:', settings.CELERY_BROKER_URL)
"
```

### Test 2: Start Celery Worker
```bash
myenv\Scripts\celery -A backend.celery_config worker -l info
```

Should show: `[*] Ready to accept tasks!`

### Test 3: Test API
```bash
curl http://localhost:8000/api/tasks
```

Should return: `{"active": 0, "scheduled": 0, "reserved": 0}`

---

## 🎯 Quick Reference: Credentials Format

### URL Format
```
redis://:PASSWORD@HOST:PORT/DB
```

### For Each Provider:

| Provider | Host | Port | Password |
|----------|------|------|----------|
| **Redis Cloud** | redis-xxxxx.c123.region.ec2.cloud.redis.io | 6379 | From "Default User" |
| **AWS ElastiCache** | your-cache.xxxxx.ng.0001.use1.cache.amazonaws.com | 6379 | Auth Token (if enabled) |
| **Azure** | your-cache.redis.cache.windows.net | 6379 | Access Key (+ `?ssl=true`) |
| **Google** | IP address | 6379 | Auth String |
| **DigitalOcean** | Host | 25061 | Password (+ `rediss://`) |
| **Heroku** | From connection string | From URL | From URL |

---

## 🚀 Complete Startup (With Hosted Redis)

Once `.env` is configured:

### Terminal 1: Start Celery Worker
```bash
cd d:\AutoDoc-Backend\docpilot-agent
myenv\Scripts\celery -A backend.celery_config worker -l info
```

### Terminal 2: Start FastAPI
```bash
cd d:\AutoDoc-Backend\docpilot-agent\backend
uvicorn main:app --reload --port 8000
```

### Terminal 3: Test
```bash
curl http://localhost:8000/api/tasks
```

**That's it! No local Redis needed!**

---

## ⚠️ Important Notes

### Security
- ✅ Store `.env` file safely (in `.gitignore`)
- ✅ Never commit `.env` to git
- ✅ Keep passwords private
- ✅ Use strong passwords provided by service

### Connection String Format
- ✅ Format: `redis://:PASSWORD@HOST:PORT/DB`
- ⚠️ Port `/DB` numbers are important! Use `/0` for broker, `/1` for backend
- ❌ Don't remove the colon `:` before password

### Common Issues
- **"Connection refused"** → Check host/port are correct
- **"WRONGPASS"** → Check password matches exactly
- **"Connection timeout"** → Check IP whitelisting in provider dashboard

---

## 💡 Recommendation

**Use Redis Cloud** for easiest setup:
1. Go to https://redis.io/try-free
2. Create free account (30 MB free tier)
3. Create database (takes 2 minutes)
4. Copy credentials from dashboard
5. Paste into `.env`
6. Done!

Cost: **Free tier available** → $2.40/month for 256MB

---

## 📞 Support Resources

- **HOSTED_REDIS_SETUP.md** - Detailed setup guide
- **Redis Cloud Docs**: https://docs.redis.com/latest/
- **Celery Docs**: https://docs.celeryproject.io/

---

**Ready to deploy with hosted Redis? You got this!** 🚀
