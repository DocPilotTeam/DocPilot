# Hosted Redis Setup Guide

## 🎯 What You Need to Provide

When using hosted Redis, you need to provide these credentials from your Redis provider:

### **Essential Credentials (Required)**
1. **Redis Host/Endpoint** - Domain or IP address
   - Example: `redis-12345.c123.us-east-1-2.ec2.cloud.redis.io`
   
2. **Redis Port** - Connection port
   - Usually: `6379` (standard)
   - Some providers use: `6380` (for SSL)
   
3. **Redis Password** - Authentication token
   - Example: `your-secure-password-here`
   - Some providers call it "Auth Token" or "Default User Password"

### **Optional Credentials (Security)**
4. **SSL/TLS Required** - Whether connection must be encrypted
   - Usually: `true` for production
   
5. **Username** - If your provider uses username+password
   - Most use just password, some use `default` as username

---

## 📋 Where to Get These Credentials

### **Option 1: Redis Cloud (Recommended - Free Tier Available)**

**Get your credentials:**

1. Go to: https://redis.io/try-free
2. Create account (free tier: 30MB)
3. Create database
4. In dashboard, click your database
5. Copy these from "General" section:
   - **Host**: `redis-xxxxx.c123.region.ec2.cloud.redis.io`
   - **Port**: `6379`
   - **Password**: Click "Default User" → Copy password

**Format for .env:**
```
CELERY_BROKER_URL=redis://:PASSWORD@HOST:PORT/0
CELERY_RESULT_BACKEND=redis://:PASSWORD@HOST:PORT/1
```

Example:
```
CELERY_BROKER_URL=redis://:your-secure-password-here@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/0
CELERY_RESULT_BACKEND=redis://:your-secure-password-here@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/1
```

---

### **Option 2: AWS ElastiCache**

**Get your credentials:**

1. Go to: https://console.aws.amazon.com/elasticache
2. Create Redis cluster
3. In cluster details, copy:
   - **Primary Endpoint**: `your-cache.xxxxx.ng.0001.use1.cache.amazonaws.com`
   - **Port**: `6379`
   - **Auth Token**: If you enabled AUTH (recommended)

**Format for .env:**
```
CELERY_BROKER_URL=redis://:AUTH_TOKEN@PRIMARY_ENDPOINT:6379/0
CELERY_RESULT_BACKEND=redis://:AUTH_TOKEN@PRIMARY_ENDPOINT:6379/1
```

**If no AUTH:**
```
CELERY_BROKER_URL=redis://PRIMARY_ENDPOINT:6379/0
CELERY_RESULT_BACKEND=redis://PRIMARY_ENDPOINT:6379/1
```

---

### **Option 3: Azure Cache for Redis**

**Get your credentials:**

1. Go to: https://portal.azure.com
2. Create "Azure Cache for Redis"
3. In "Access Keys" section, copy:
   - **Primary Connection String** 
   - Or **Primary Endpoint** and **Primary Access Key**

**Format for .env:**

If you have connection string:
```
CELERY_BROKER_URL=redis://default:PRIMARY_KEY@HOSTNAME:6379/0?ssl=true
CELERY_RESULT_BACKEND=redis://default:PRIMARY_KEY@HOSTNAME:6379/1?ssl=true
```

If you have endpoint and key separately:
```
CELERY_BROKER_URL=redis://default:YOUR_ACCESS_KEY@your-cache.redis.cache.windows.net:6379/0?ssl=true
CELERY_RESULT_BACKEND=redis://default:YOUR_ACCESS_KEY@your-cache.redis.cache.windows.net:6379/1?ssl=true
```

---

### **Option 4: Google Cloud Memorystore**

**Get your credentials:**

1. Go to: https://console.cloud.google.com/memorystore
2. Create Redis instance
3. Copy:
   - **IP Address**: `10.0.0.3` or public IP
   - **Port**: `6379`
   - **Auth String**: If enabled

**Format for .env:**
```
CELERY_BROKER_URL=redis://:AUTH_STRING@IP_ADDRESS:6379/0
CELERY_RESULT_BACKEND=redis://:AUTH_STRING@IP_ADDRESS:6379/1
```

---

### **Option 5: Heroku Redis**

**Get your credentials:**

1. Run: `heroku addons:create heroku-redis:premium-0`
2. Get URL: `heroku config:get REDIS_URL`
3. Copy the Redis URL

**Format for .env:**
```
CELERY_BROKER_URL=REDIS_URL_FROM_HEROKU/0
CELERY_RESULT_BACKEND=REDIS_URL_FROM_HEROKU/1
```

---

### **Option 6: DigitalOcean Managed Redis**

**Get your credentials:**

1. Go to: https://cloud.digitalocean.com/databases
2. Create Managed Redis cluster
3. In connection details, copy:
   - **Connection String**: `rediss://default:PASSWORD@HOST:PORT`
   - Or **Host**, **Port**, **Password** separately

**Format for .env:**
```
CELERY_BROKER_URL=rediss://default:PASSWORD@HOST:25061/0
CELERY_RESULT_BACKEND=rediss://default:PASSWORD@HOST:25061/1
```

---

## 🔧 Configuration Setup

### Step 1: Create Hosted Redis Instance

Choose any provider above and create your Redis database. Collect these 3 things:
- ✅ Host
- ✅ Port
- ✅ Password

### Step 2: Update .env File

Open your `.env` file and update:

```env
# OLD (Local)
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/1

# NEW (Hosted)
CELERY_BROKER_URL=redis://:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/0
CELERY_RESULT_BACKEND=redis://:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/1
```

**Example with Redis Cloud:**
```env
CELERY_BROKER_URL=redis://:user123password456@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/0
CELERY_RESULT_BACKEND=redis://:user123password456@redis-12345.c123.us-east-1-2.ec2.cloud.redis.io:6379/1
```

### Step 3: Update Connection Pool (Optional but Recommended)

Edit `backend/celery_config.py`:

```python
app.conf.update(
    # ... existing config ...
    
    # Add these for hosted Redis:
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Connection pool settings for hosted Redis
    broker_pool_limit=None,
    broker_channel_error_retry=5.0,
)
```

This ensures your connection stays stable with hosted Redis.

---

## ✅ Verification Steps

### Test 1: Verify Configuration Loads
```bash
myenv\Scripts\python -c "
from backend.core.config import settings
print(f'Broker URL: {settings.CELERY_BROKER_URL}')
print(f'Backend URL: {settings.CELERY_RESULT_BACKEND}')
"
```

### Test 2: Test Redis Connection
```bash
myenv\Scripts\python -c "
import redis
from backend.core.config import settings

# Parse Redis URL
import re
match = re.match(r'redis://:(.+)@(.+):(\d+)/(\d+)', settings.CELERY_BROKER_URL)
if match:
    password, host, port, db = match.groups()
    r = redis.Redis(host=host, port=int(port), password=password, db=int(db))
    result = r.ping()
    print(f'✓ Redis connection OK: {result}')
else:
    print('✗ Invalid Redis URL format')
"
```

### Test 3: Start Celery Worker
```bash
myenv\Scripts\celery -A backend.celery_config worker -l info
```

Should show:
```
[*] Ready to accept tasks!
```

---

## 🔒 Security Best Practices

### 1. Never Commit Credentials
- ✅ Use `.env` file (already in `.gitignore`)
- ✅ Don't share `.env` publicly
- ❌ Don't put credentials in code

### 2. Use Strong Passwords
- ✅ Most providers generate secure passwords
- ✅ Change default passwords
- ❌ Don't use "password123"

### 3. Enable SSL/TLS
- ✅ Use `rediss://` (with SSL) when available
- ✅ Most hosted services support/require this
- ❌ Use plain `redis://` only for testing

### 4. Enable Auth Token
- ✅ All hosted services support authentication
- ✅ Always use a password
- ❌ Never disable authentication

### 5. Restrict Network Access
- ✅ Whitelist your app's IP address
- ✅ Use VPC/private networks when available
- ❌ Don't allow access from anywhere

---

## 💰 Cost Comparison

| Provider | Free Tier | Starting Price | Notes |
|----------|-----------|-----------------|-------|
| **Redis Cloud** | 30 MB | $12.93/month | Recommended for small apps |
| **AWS ElastiCache** | 750 hrs/month | Pay-as-you-go | Cheapest for heavy usage |
| **Azure Cache** | - | $13/month | Good if using Azure |
| **Google Memorystore** | - | $5.13/month | Cheapest monthly |
| **Heroku Redis** | - | $15/month | Easy if using Heroku |
| **DigitalOcean** | - | $5/month | Best value for small apps |

---

## 📝 Information Checklist

**From your Redis provider, collect these 3 items:**

- [ ] **Host/Endpoint**: `_________________________`
- [ ] **Port**: `_________________________`
- [ ] **Password**: `_________________________`

**Then create .env entry:**
```
CELERY_BROKER_URL=redis://:PASSWORD@HOST:PORT/0
CELERY_RESULT_BACKEND=redis://:PASSWORD@HOST:PORT/1
```

---

## 🚀 Full Startup with Hosted Redis

Once configured:

### Terminal 1: Celery Worker
```bash
cd d:\AutoDoc-Backend\docpilot-agent
myenv\Scripts\celery -A backend.celery_config worker -l info
```

### Terminal 2: FastAPI
```bash
cd d:\AutoDoc-Backend\docpilot-agent\backend
uvicorn main:app --reload --port 8000
```

### Terminal 3: Test
```bash
curl http://localhost:8000/api/tasks
```

**No local Redis needed!** ✓

---

## 🆘 Troubleshooting

### Issue: "Connection refused"
```
Error: Error 10061 connecting to redis host
```
**Check:**
- ✅ Redis instance is running in your provider's dashboard
- ✅ Credentials are correct in `.env`
- ✅ Your IP is whitelisted (if provider requires)
- ✅ Connection string format is correct

### Issue: "Authentication failed"
```
Error: WRONGPASS invalid username-password pair
```
**Check:**
- ✅ Password in `.env` exactly matches provider
- ✅ Using correct format: `redis://:PASSWORD@HOST:PORT/DB`
- ✅ No spaces in password in `.env`

### Issue: "SSL certificate problem"
```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```
**Solution:** Add SSL verification disable (NOT recommended for production):
```python
# In celery_config.py, add:
app.conf.broker_use_ssl = {
    'ssl_certfile': None,
    'ssl_keyfile': None,
    'ssl_ca_certs': None,
    'ssl_cert_reqs': 'none'  # Only for testing!
}
```

Better solution: Use proper SSL certificates

---

## 📚 Additional Resources

- **Redis Cloud Docs**: https://docs.redis.com/latest/
- **AWS ElastiCache**: https://docs.aws.amazon.com/elasticache/
- **Azure Cache**: https://docs.microsoft.com/azure/azure-cache-for-redis/
- **Celery Redis Broker**: https://docs.celeryproject.io/en/stable/brokers/redis.html

---

## ✨ Summary

**What You Need to Do:**

1. ✅ Choose a hosted Redis provider (Redis Cloud recommended for free tier)
2. ✅ Create a Redis instance
3. ✅ Collect: Host, Port, Password
4. ✅ Update `.env` with connection string
5. ✅ Test connection with provided verification script
6. ✅ No local Redis needed anymore!

Your application is now production-ready with hosted Redis! 🎉
