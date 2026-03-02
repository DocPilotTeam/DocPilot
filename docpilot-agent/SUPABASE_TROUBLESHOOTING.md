# Supabase Connection Error: [Errno 11001] getaddrinfo failed

## What This Error Means

**[Errno 11001] getaddrinfo failed** is a Windows DNS resolution error. It occurs when your system cannot resolve the Supabase hostname to an IP address.

This typically happens during:
1. User registration/login (storing user data)
2. Repository information storage
3. Documentation retrieval/storage

## Root Causes

| Cause | Indicators | Solution |
|-------|-----------|----------|
| **No Internet Connection** | Can't access any website | Check WiFi/network connection |
| **Firewall/Proxy Blocking** | Other sites work but not Supabase | Configure firewall/proxy settings |
| **Invalid Supabase URL** | `SUPABASE_URL` malformed in .env | Verify correct Supabase project URL |
| **Missing API Key** | `SUPABASE_SERVICE_KEY` not set | Add API key to .env file |
| **DNS Server Issues** | DNS fails for this domain only | Change DNS servers (8.8.8.8, 1.1.1.1) |
| **Corporate Network** | Behind corporate proxy | Configure proxy in .env or system |

## Step-by-Step Troubleshooting

### Step 1: Run Supabase Diagnostic Test

This script will test your Supabase configuration:

```bash
# Activate virtual environment
.\venv\Scripts\activate.ps1

# Run diagnostic test
python test_supabase_connectivity.py
```

This will check:
- ✅ DNS resolution to Supabase
- ✅ HTTPS connectivity
- ✅ API authentication
- ✅ Python client initialization
- ✅ Environment variables
- ✅ Database table accessibility

### Step 2: Verify Supabase Configuration

**A) Check .env file has Supabase credentials:**

```dotenv
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_SERVICE_KEY="sbp_service_your_secret_key_here"
```

**B) Get correct values from Supabase:**

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to Settings → API
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **Service Role Key** → `SUPABASE_SERVICE_KEY`

**C) Verify URL format:**

```
✅ Correct: https://abcdefgh.supabase.co
❌ Wrong: abcdefgh.supabase.co (missing https://)
❌ Wrong: https://abcdefgh.supabase.co/ (trailing slash)
```

### Step 3: Test Network Connectivity

Test if your system can reach Supabase:

```powershell
# Test DNS resolution
[System.Net.Dns]::GetHostAddresses("your-project.supabase.co")

# Test HTTPS connection (should show response)
Invoke-WebRequest -Uri "https://your-project.supabase.co/rest/v1/" -UseBasicParsing
```

Expected: DNS resolves to an IP, HTTPS returns 403 (access denied is ok - we just need connectivity)

### Step 4: Check Firewall Settings

**Windows Defender Firewall:**

```powershell
# Check if Python is allowed through firewall
netsh advfirewall firewall show rule name=all | findstr /I "python"

# Allow Python (if blocked)
New-NetFirewallRule -DisplayName "Allow Python HTTPS" `
  -Direction Outbound -Program "C:\path\to\python.exe" `
  -Action Allow -Protocol TCP -RemotePort 443
```

**Third-party Firewalls:**
- Zscaler, Palo Alto Networks, Fortinet, etc.
- Add to whitelist:
  - Domain: `*.supabase.co`
  - Protocol: HTTPS (port 443)

### Step 5: Verify Database Tables Exist

Supabase requires specific tables to exist. Check if tables exist:

```bash
# In Supabase dashboard → SQL Editor, run:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

You need these tables:
```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_id INT UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Repos table
CREATE TABLE IF NOT EXISTS repos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proj_name VARCHAR(255) NOT NULL,
    repo_url TEXT NOT NULL,
    branch VARCHAR(255) DEFAULT 'main',
    auth_token TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Documentation table
CREATE TABLE IF NOT EXISTS documentation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proj_name VARCHAR(255) NOT NULL,
    repo_url TEXT,
    content TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    generated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Step 6: Configure Proxy (if needed)

If behind a corporate proxy, add to `.env`:

```dotenv
# Supabase Proxy Configuration
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
NO_PROXY=localhost,127.0.0.1
```

Then the Python client will use the proxy automatically.

### Step 7: Test with Python

```python
from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

# Try to create client
client = create_client(url, key)

# Try to query users table
try:
    result = client.table("users").select("*").limit(1).execute()
    print("✅ Connection successful!")
    print(f"Response: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Solution: Automatic Retry Logic

I've added **automatic retry logic** to all database operations:

✅ **Max 3 retry attempts** - Tolerates transient network issues  
✅ **Exponential backoff** - 1s, 2s, 3s delays between retries  
✅ **Smart retry detection** - Only retries on network/DNS errors  
✅ **Detailed logging** - Shows exactly what failed and why  
✅ **Human-readable errors** - Clear messages instead of technical jargon  

## Testing the Fix

1. **Run diagnostic test first:**
```bash
.\venv\Scripts\activate.ps1
python test_supabase_connectivity.py
```

2. **Check output** for any failures
3. **Fix any issues** shown in diagnostic
4. **Restart FastAPI:**
```bash
.\venv\Scripts\activate.ps1
python -m uvicorn backend.main:app --reload
```

5. **Try GitHub OAuth again:**
```
http://localhost:8000/auth/login/github
```

## Understanding the New Error Handling

**Before:** Generic error `"Failed to create user session: [Errno 11001] getaddrinfo failed"`

**After:** Clear, specific error messages:
- `"Failed to connect to Supabase: DNS resolution failed for phargickpgzoomnwlnhd.supabase.co"`
- `"Network error in upsert_user (attempt 1/3): getaddrinfo failed"`
- `"Retrying in 1 seconds..." → `"Retrying in 2 seconds..." → etc.

## Common Scenarios

### Scenario 1: Works at Home, Fails at Work
**Cause:** Corporate proxy blocking  
**Solution:** Configure proxy in .env or system settings

### Scenario 2: Intermittent Failures
**Cause:** Transient network issues  
**Solution:** Automatic retry logic now handles this (built in)

### Scenario 3: Always Fails on This Computer
**Cause:** Firewall rules or DNS issues  
**Solution:** 
- Whitelist Python in firewall
- Change DNS to 8.8.8.8 or 1.1.1.1
- Test from different network

### Scenario 4: Works in PowerShell, Fails in Python
**Cause:** Different network stack or proxy settings  
**Solution:** Check system-wide proxy configuration

## File Changes

### Updated Files:
- `backend/db/supabase_client.py` - Better error messages
- `backend/users/user_queries.py` - Automatic retry logic
- `backend/db/repo_queries.py` - Automatic retry logic

### New Files:
- `test_supabase_connectivity.py` - Diagnostic script
- `SUPABASE_TROUBLESHOOTING.md` - This guide

## Additional Resources

- Supabase Docs: https://supabase.com/docs
- Python Supabase Client: https://github.com/supabase-community/supabase-py
- Network Troubleshooting: https://learn.microsoft.com/en-us/windows/client-management/troubleshoot-tcpip

