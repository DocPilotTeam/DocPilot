# GitHub OAuth Error: [Errno 11001] getaddrinfo failed

## What This Error Means

**[Errno 11001] getaddrinfo failed** is a Windows DNS resolution error. It occurs when your system cannot resolve the hostname `github.com` or `api.github.com` to an IP address.

This happens in the OAuth flow when DocPilot tries to:
1. Exchange the authorization code for an access token
2. Fetch your GitHub user profile
3. Fetch your repositories list

## Common Causes

| Cause | Solution |
|-------|----------|
| **No Internet Connection** | Check your network connection. Try pinging `github.com` from command prompt. |
| **Firewall Blocking HTTPS** | Configure your firewall to allow outbound HTTPS (port 443) to github.com |
| **Corporate Proxy** | If behind a corporate proxy, configure proxy settings in your .env file |
| **DNS Server Issues** | Try changing DNS to 8.8.8.8 (Google) or 1.1.1.1 (Cloudflare) |
| **Invalid GitHub Credentials** | Verify `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in .env file |
| **VPN/Proxy Issues** | Disconnect VPN or configure proxy if required |

## Step-by-Step Troubleshooting

### Step 1: Run Diagnostic Test

This script will test your network connectivity to GitHub:

```bash
# Activate virtual environment first
.\venv\Scripts\activate.ps1

# Run the diagnostic test
python test_github_connectivity.py
```

This will check:
- ✅ DNS resolution to github.com
- ✅ HTTPS connectivity
- ✅ GitHub OAuth endpoint reachability
- ✅ Environment variable configuration
- ✅ Proxy settings

### Step 2: Test Basic Network Access

In PowerShell, test if you can reach GitHub:

```powershell
# Test DNS resolution
[System.Net.Dns]::GetHostAddresses("github.com")

# Test HTTPS connection (should show SSL cert info)
Invoke-WebRequest -Uri "https://api.github.com" -UseBasicParsing

# Or use curl if available
curl https://api.github.com
```

Expected output: Should return GitHub's IP address and no connection errors.

### Step 3: Check Firewall

**Windows Defender Firewall:**

```powershell
# Allow Python through firewall
New-NetFirewallRule -DisplayName "Allow Python HTTPS" -Direction Outbound -Program "C:\path\to\python.exe" -Action Allow -Protocol TCP -RemotePort 443

# Or check if blocked
netsh advfirewall firewall show rule name=all | findstr /I "python"
```

**Third-party Firewalls (Zscaler, Palo Alto, etc):**
- Add `github.com` and `api.github.com` to whitelist
- Allow TCP port 443 (HTTPS)

### Step 4: Verify GitHub OAuth Credentials

1. Go to: https://github.com/settings/developers
2. Click your OAuth App
3. Verify these values match your `.env` file:
   - **Client ID** → `GITHUB_CLIENT_ID`
   - **Client Secret** → `GITHUB_CLIENT_SECRET`
   - **Authorization callback URL** → `GITHUB_REDIRECT_URI` (should be `http://localhost:8000/auth/github/callback`)

### Step 5: Configure Proxy (if behind corporate proxy)

If you're behind a corporate proxy, add these to your `.env` file:

```dotenv
# Proxy Configuration (if needed)
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
NO_PROXY=localhost,127.0.0.1,.company.com
```

Then use the enhanced code that includes proxy support:

```python
async with httpx.AsyncClient(
    proxy="http://proxy.company.com:8080",
    verify=ssl_context,
    timeout=30.0
) as client:
    # requests will go through proxy
```

### Step 6: Test with cURL

```bash
# Test OAuth endpoint
curl -X POST https://github.com/login/oauth/access_token \
  -H "Accept: application/json" \
  -d "client_id=YOUR_CLIENT_ID&client_secret=YOUR_SECRET&code=test"

# Should get a response (error is ok, we're just testing connectivity)
```

## Solution: Enhanced Code

I've updated your GitHub authentication module with:

✅ **Proper SSL context** - Handles Windows SSL verification correctly  
✅ **Explicit timeouts** - 30-second timeout for network calls  
✅ **Better error messages** - Clear, actionable error responses  
✅ **Detailed logging** - Tracks each step for debugging  
✅ **Graceful fallbacks** - Continues without repos if they fail to load  
✅ **Request validation** - Checks responses before parsing

## Testing the Fix

1. **Restart FastAPI Server:**
```bash
.\venv\Scripts\activate.ps1
python -m uvicorn backend.main:app --reload
```

2. **Try OAuth again:**
```
http://localhost:8000/auth/login/github
```

3. **Check logs** for detailed error messages with the new logging

## If Error Persists

If you still see `[Errno 11001] getaddrinfo failed`:

1. **Run diagnostic test**: `python test_github_connectivity.py`
2. **Check Windows Event Viewer** for network errors
3. **Try from different network** (home WiFi vs corporate)
4. **Verify GitHub OAuth app** exists and is configured correctly
5. **Check Python version** - ensure httpx and dependencies are compatible

## Advanced: SSLError Debugging

If you get SSL certificate errors, try this temporary fix (development only):

```python
# In backend/auth/github.py - NOT RECOMMENDED FOR PRODUCTION
async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
    # verify=False disables SSL verification (insecure!)
```

For production, properly install system certificates:

```bash
# Windows: Install certificates
python -m certifi
certifi.where()

# Or use Windows native certificate store
```

## Common Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `[Errno 11001] getaddrinfo failed` | DNS resolution failed | Check internet, firewall, DNS settings |
| `SSLError` | Certificate validation failed | Update certificates or use proper CA bundle |
| `TimeoutError` | Network request took too long | Increase timeout, check network speed |
| `401 Unauthorized` | Invalid GitHub credentials | Verify CLIENT_ID/SECRET in .env |
| `403 Forbidden` | Rate limited or insufficient permissions | Wait 1 hour or verify OAuth scope |

## More Help

- GitHub OAuth Docs: https://docs.github.com/en/developers/apps/building-oauth-apps
- httpx Documentation: https://www.python-httpx.org/
- Windows Proxy Setup: https://learn.microsoft.com/en-us/windows/win32/wininet/About-WinINet

