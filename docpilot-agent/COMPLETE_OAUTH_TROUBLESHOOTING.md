# Complete OAuth Flow Troubleshooting Guide

## Overview of the GitHub OAuth Flow

When you visit `http://localhost:8000/auth/login/github`, here's what happens:

```
1. User clicks login
   ↓
2. Redirected to GitHub OAuth page
   ↓
3. User authorizes DocPilot
   ↓
4. GitHub redirects to: /auth/github/callback?code=123...
   ↓
5. Exchange code for access token (GitHub API call)
   ↓
6. Fetch user profile (GitHub API call)
   ↓
7. Fetch repositories (GitHub API call)
   ↓
8. Store user in Supabase (Database write)
   ↓
9. Retrieve user from Supabase (Database read)
   ↓
10. Create JWT token
    ↓
11. Return token to user
```

## Error Diagnosis by Stage

### Stage 1-4: GitHub Redirect
**Error**: None expected (browser handles this)  
**If fails**: GitHub OAuth app not configured correctly

### Stage 5: Code Exchange
**Error**: `[Errno 11001] getaddrinfo failed`  
**Cause**: Can't reach `github.com`  
**Fix**: Run `python test_github_connectivity.py`

### Stage 6: Fetch User Profile
**Error**: `[Errno 11001] getaddrinfo failed`  
**Cause**: Can't reach `api.github.com`  
**Fix**: Same as Stage 5

### Stage 7: Fetch Repositories
**Error**: May fail silently (non-critical)  
**Cause**: GitHub API network issues  
**Fix**: App continues without repos

### Stage 8: Store User in Supabase
**Error**: `[Errno 11001] getaddrinfo failed` (your current issue)  
**Cause**: Can't reach Supabase database  
**Fix**: Run `python test_supabase_connectivity.py`

### Stage 9: Retrieve User from Supabase
**Error**: `[Errno 11001] getaddrinfo failed`  
**Cause**: Can't reach Supabase database  
**Fix**: Same as Stage 8

### Stage 10-11: Token Creation & Response
**Error**: Rarely fails (local operation)  
**Cause**: JWT secret not configured  
**Fix**: Check `.env` has `JWT_SECRET` set

## Quick Diagnosis Checklist

### ✅ Prerequisites
- [ ] Internet connection working
- [ ] Can access https://github.com and https://supabase.com
- [ ] Firewall allows HTTPS (port 443)
- [ ] Python 3.8+ installed
- [ ] Virtual environment activated

### ✅ GitHub Configuration
- [ ] `GITHUB_CLIENT_ID` set in .env
- [ ] `GITHUB_CLIENT_SECRET` set in .env
- [ ] `GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback`
- [ ] OAuth app exists at https://github.com/settings/developers

### ✅ Supabase Configuration
- [ ] `SUPABASE_URL` set in .env
- [ ] `SUPABASE_SERVICE_KEY` set in .env
- [ ] Tables exist: `users`, `repos`, `documentation`
- [ ] Can access Supabase dashboard

### ✅ Network Configuration
- [ ] No proxy blocking (or proxy configured)
- [ ] DNS working correctly
- [ ] Firewall allows Python outbound HTTPS

## Testing Procedure

Follow this step-by-step to identify the issue:

### Step 1: Test GitHub API
```bash
.\venv\Scripts\activate.ps1
python test_github_connectivity.py
```

**Expected output:**
```
✅ PASS: DNS Resolution
✅ PASS: HTTPS Connection
✅ PASS: OAuth Endpoint
✅ PASS: GitHub Config
✅ PASS: Proxy Settings
```

If any fails: Fix the GitHub issue before proceeding

### Step 2: Test Supabase API
```bash
python test_supabase_connectivity.py
```

**Expected output:**
```
✅ PASS: DNS Resolution
✅ PASS: HTTPS Connection
✅ PASS: Supabase Auth
✅ PASS: Client Init
✅ PASS: Environment
✅ PASS: Database Tables
```

If any fails: Fix the Supabase issue before proceeding

### Step 3: Test FastAPI Server
```bash
python -m uvicorn backend.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Try OAuth Flow
1. Visit: http://localhost:8000/auth/login/github
2. Click "Sign in with GitHub"
3. Authorize the app
4. Check response

### Step 5: Check Logs
```bash
# Look for detailed error messages showing:
# - Which stage failed
# - Why it failed
# - What to do to fix it
```

## Common Error Messages & Fixes

### `[Errno 11001] getaddrinfo failed`
**Location**: First appears in Stage 5-7 (GitHub)
**Cause**: DNS/network issue reaching GitHub
**Solution**:
```bash
# Test GitHub connectivity
python test_github_connectivity.py

# Check DNS
[System.Net.Dns]::GetHostAddresses("api.github.com")

# Check firewall
netsh advfirewall firewall show rule name=all | findstr HTTPs
```

### `[Errno 11001] getaddrinfo failed` (at Stage 8)
**Location**: When storing user in Supabase
**Cause**: DNS/network issue reaching Supabase
**Solution**:
```bash
# Test Supabase connectivity
python test_supabase_connectivity.py

# Check Supabase credentials
echo $env:SUPABASE_URL
echo $env:SUPABASE_SERVICE_KEY

# Verify database connection
python -c "from backend.db.supabase_client import supabase; print('OK')"
```

### `SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]`
**Cause**: SSL certificate validation issue
**Solution** (for development):
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

**Better solution** (for production):
```bash
# Update Python certificates
python -m certifi

# Or on Windows
certifi.where()  # Find certificate location
```

### `401 Unauthorized` from GitHub
**Cause**: Invalid CLIENT_ID or CLIENT_SECRET
**Solution**:
1. Go to https://github.com/settings/developers
2. Verify OAuth App exists
3. Copy correct ID and Secret to .env
4. Restart server

### `403 Forbidden` from GitHub
**Cause**: Rate limited or insufficient OAuth scope
**Solution**:
```python
# In backend/auth/router.py, OAuth scope includes:
# scope=repo read:user

# Wait 1 hour for rate limit reset
# Or create new OAuth app with different credentials
```

### `Connection refused` or `Connection timeout`
**Cause**: Service not running or firewall blocking
**Solution**:
```bash
# Verify GitHub/Supabase are accessible
curl https://api.github.com
curl https://your-project.supabase.co/rest/v1/

# Check firewall logs
# Whitelist domain if needed
```

## Network Debugging Commands

### PowerShell Commands
```powershell
# Test DNS resolution
[System.Net.Dns]::GetHostAddresses("api.github.com")
[System.Net.Dns]::GetHostAddresses("your-project.supabase.co")

# Test HTTPS connection
Invoke-WebRequest -Uri "https://api.github.com" -UseBasicParsing
Invoke-WebRequest -Uri "https://your-project.supabase.co/rest/v1/" -UseBasicParsing

# Check firewall rules
netsh advfirewall firewall show rule name=all | findstr /I "python"

# Trace route to server
tracert api.github.com
```

### Python Commands
```python
# Test DNS from Python
import socket
socket.gethostbyname("api.github.com")

# Test HTTPS
import httpx
httpx.get("https://api.github.com")

# Test async HTTPS  
import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.github.com")
        print(r.status_code)

asyncio.run(test())
```

## Environment Variables Reference

```dotenv
# GitHub OAuth
GITHUB_CLIENT_ID=Ov23li6rGorVW2pn01Xc
GITHUB_CLIENT_SECRET=4ea284203ffdbc7884154606761d0ca340f70612
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Supabase
SUPABASE_URL=https://phargickpgzoomnwlnhd.supabase.co
SUPABASE_SERVICE_KEY=sbp_service_your_long_secret_key
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres

# JWT
JWT_SECRET=your_jwt_secret_key_here
JWT_ALGORITHM=HS256

# Proxy (if needed)
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
NO_PROXY=localhost,127.0.0.1,.company.internal
```

## Recovery Steps

If the OAuth flow fails:

### 1. Don't panic! This is normal during setup.

### 2. Identify which stage failed:
- Run diagnostic tests
- Check logs for error messages
- Match error to the checklist above

### 3. Fix the issue:
- Network: Check firewall, proxy, DNS
- Credentials: Verify .env values
- Configuration: Check GitHub/Supabase settings

### 4. Restart services:
```bash
# Stop FastAPI (Ctrl+C)
# Stop Celery (if running)

# Start fresh
.\venv\Scripts\activate.ps1
python -m uvicorn backend.main:app --reload
```

### 5. Try again:
```
http://localhost:8000/auth/login/github
```

## Getting Help

If you're still stuck:

1. **Save the error message** - Get the full error text
2. **Check logs** - Look for detailed error information
3. **Run diagnostics** - Both GitHub and Supabase tests
4. **Share the output** - Include test results and error messages

**Helpful information to share:**
- Full error message
- Output of diagnostic tests
- Your .env file (with secrets redacted)
- Your network setup (proxy, VPN, firewall)
- Your location (home, office, etc.)

## Next Steps

Once OAuth is working:

1. ✅ GitHub login should work
2. ✅ User profile should load
3. ✅ Repositories should list
4. ✅ Browse the dashboard

Then you can:
- Configure webhooks for CI/CD
- Start analyzing repositories
- Generate documentation automatically

Happy coding! 🚀
