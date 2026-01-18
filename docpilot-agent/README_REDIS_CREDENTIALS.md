# 📋 REDIS CREDENTIALS - What to Provide (One Page)

## ✅ You Need Exactly 3 Things

```
╔════════════════════════════════════════════════════════════════╗
║                    YOUR CREDENTIALS                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  1. REDIS HOST/ENDPOINT                                        ║
║     ┌─────────────────────────────────────────────────────┐   ║
║     │ redis-12345.c123.us-east-1-2.ec2.cloud.redis.io     │   ║
║     └─────────────────────────────────────────────────────┘   ║
║                                                                ║
║  2. REDIS PORT                                                 ║
║     ┌─────────────────────────────────────────────────────┐   ║
║     │ 6379                                                │   ║
║     └─────────────────────────────────────────────────────┘   ║
║                                                                ║
║  3. REDIS PASSWORD                                             ║
║     ┌─────────────────────────────────────────────────────┐   ║
║     │ abc123def456ghi789                                  │   ║
║     │ ⚠️ KEEP THIS SECRET!                                │   ║
║     └─────────────────────────────────────────────────────┘   ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 🎯 Top 3 Providers (Ranked)

### **#1 REDIS CLOUD** ⭐ RECOMMENDED
```
✅ Free tier: 30 MB
✅ Setup: 5 minutes
✅ No credit card needed
✅ Easy dashboard

Step 1: Visit https://redis.io/try-free
Step 2: Create free account
Step 3: Click "Create Database"
Step 4: Copy Host, Port, Password
Step 5: Add to .env
Step 6: Done!
```

### **#2 AWS ELASTICACHE**
```
✅ Pay as you go
✅ 750 hours free tier
✅ Good if using AWS

Step 1: AWS Console → ElastiCache
Step 2: Create Redis cluster
Step 3: Copy Primary Endpoint
Step 4: Copy Auth Token (optional but recommended)
Step 5: Add to .env
```

### **#3 DIGITALOCEAN MANAGED REDIS**
```
✅ Cheapest paid: $5/month
✅ 5 minute setup
✅ Simple dashboard

Step 1: DigitalOcean → Databases
Step 2: Create Redis cluster
Step 3: Copy connection details
Step 4: Extract Host, Port, Password
Step 5: Add to .env
```

---

## 🔧 Adding to Your Code

### **Open this file:**
```
d:\AutoDoc-Backend\docpilot-agent\.env
```

### **Find this:**
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### **Replace with:**
```env
CELERY_BROKER_URL=redis://:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/0
CELERY_RESULT_BACKEND=redis://:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/1
```

### **Real Example:**
```env
CELERY_BROKER_URL=redis://:abc123def456ghi789@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/0
CELERY_RESULT_BACKEND=redis://:abc123def456ghi789@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/1
```

---

## ✔️ Verification

### **Test 1: Check Configuration**
```bash
myenv\Scripts\python -c "from backend.core.config import settings; print(settings.CELERY_BROKER_URL[:20] + '...')"
```
Should show your Redis URL (partially)

### **Test 2: Start Worker**
```bash
myenv\Scripts\celery -A backend.celery_config worker -l info
```
Should show: `[*] Ready to accept tasks!`

### **Test 3: Test API**
```bash
curl http://localhost:8000/api/tasks
```
Should return: `{"active": 0, "scheduled": 0, "reserved": 0}`

---

## 📋 Copy-Paste Template

Fill this in and you're done:

```env
# From your Redis provider, fill in these 3 values:

# 1. Copy from provider dashboard:
REDIS_HOST=_____________________________

# 2. Copy from provider dashboard:
REDIS_PORT=_____________________________

# 3. Copy from provider dashboard (SECRET!):
REDIS_PASSWORD=_____________________________

# Then use this format in .env:
CELERY_BROKER_URL=redis://:REDIS_PASSWORD@REDIS_HOST:REDIS_PORT/0
CELERY_RESULT_BACKEND=redis://:REDIS_PASSWORD@REDIS_HOST:REDIS_PORT/1

# Final example:
# CELERY_BROKER_URL=redis://:abc123@redis.example.com:6379/0
# CELERY_RESULT_BACKEND=redis://:abc123@redis.example.com:6379/1
```

---

## 🚀 Complete Startup

After updating `.env`:

```bash
# Terminal 1: Start Celery Worker
cd d:\AutoDoc-Backend\docpilot-agent
myenv\Scripts\celery -A backend.celery_config worker -l info

# Terminal 2: Start API (keep running)
cd d:\AutoDoc-Backend\docpilot-agent\backend
uvicorn main:app --reload --port 8000

# Terminal 3: Test
curl http://localhost:8000/api/tasks
```

---

## 🎯 Format Guide

### ✅ CORRECT FORMATS:
```
redis://:password@host:6379/0
redis://:mypass@redis.example.com:6379/0
redis://:abc123@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/0
rediss://:password@host:25061/0  (SSL - DigitalOcean)
```

### ❌ WRONG FORMATS:
```
redis://host:6379/0              (missing :password@)
redis://password@host:6379/0     (missing : before password)
redis://:password@host:port/0    (port not a number)
redis://:password@host:6379      (missing /0)
redis://localhost:6379/0         (don't use localhost, use host!)
```

---

## ⚠️ Important

| ✅ DO | ❌ DON'T |
|------|---------|
| Copy password exactly | Add spaces or extra characters |
| Use `/0` for broker | Forget the database number |
| Use `/1` for results | Reuse same database |
| Keep .env safe | Commit to git |
| Use strong passwords | Share with others |

---

## 🆘 Quick Troubleshooting

| Error | Solution |
|-------|----------|
| "Connection refused" | Check host/port are correct |
| "WRONGPASS" | Copy password again exactly |
| "Timeout connecting" | Check IP whitelisting in provider |
| "Can't import config" | Make sure .env exists in correct folder |

---

## 📞 Need Help?

See these files for detailed info:
- `REDIS_QUICK_REFERENCE.md` - One page overview
- `HOSTED_REDIS_SETUP.md` - Detailed per-provider setup
- `REDIS_CREDENTIALS_CHECKLIST.md` - Step-by-step checklist

---

## 🎉 That's All!

Once you provide these 3 values, your application is **production-ready**! 

No more local Redis needed. Deploy with confidence. 🚀

---

**NEXT: Choose a provider and get your 3 values!**
