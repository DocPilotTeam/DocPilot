# How to Start Redis on Windows

## Option 1: Using Windows Subsystem for Linux (WSL) - Recommended

```bash
# In PowerShell/Command Prompt:
wsl redis-server
```

**Then in another terminal, keep it running in background:**
```bash
# This will keep Redis running
# Leave this terminal open
```

---

## Option 2: Install Memurai (Windows Native Redis)

1. Download from: https://github.com/microsoftarchive/memurai-db/releases
2. Download the `.msi` installer
3. Run installer
4. Start Redis:
   ```bash
   redis-server
   ```

---

## Option 3: Using Docker

```bash
docker run -d -p 6379:6379 redis:latest
```

---

## Verify Redis is Running

In a new terminal:
```bash
redis-cli ping
```

**Expected output:**
```
PONG
```

---

## Quick Setup (Recommended for Testing)

### Step 1: Start Redis
Open a PowerShell terminal and run:
```bash
wsl redis-server
```

Leave this window open - it's running Redis in the background.

### Step 2: Verify Redis Works
Open a **NEW** PowerShell terminal and run:
```bash
wsl redis-cli ping
```

Should return: `PONG`

### Step 3: Start Celery Worker
Open a **NEW** PowerShell terminal:
```bash
cd d:\AutoDoc-Backend\docpilot-agent
myenv\Scripts\celery -A backend.celery_config worker -l info
```

Wait for: `[*] Ready to accept tasks!`

### Step 4: Start FastAPI (if not already running)
Open a **NEW** PowerShell terminal:
```bash
cd d:\AutoDoc-Backend\docpilot-agent
cd backend
uvicorn main:app --reload --port 8000
```

### Step 5: Test
Open browser: http://localhost:8000/docs

---

## Terminal Setup Summary

You should have **3-4 terminals running**:

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `wsl redis-server` | Redis broker (leave running) |
| 2 | `celery -A backend.celery_config worker -l info` | Task worker |
| 3 | `uvicorn main:app --reload --port 8000` | API server |
| 4 (Optional) | `celery -A backend.celery_config flower` | Monitoring UI |

---

## Troubleshooting

### "redis-cli is not recognized"
**Solution:** Use WSL version:
```bash
wsl redis-cli ping
```

### "WSL not installed"
**Solution:** Enable WSL:
```bash
# Run in PowerShell as Admin:
wsl --install
```

Then restart and try again.

### "Connection refused on port 6379"
**Solution:** Redis is not running. Follow Step 1 above.

### "Cannot connect after WSL redis-server starts"
**Solution:** Use WSL redis-cli to test:
```bash
wsl redis-cli ping
```

Should return: `PONG`

---

## Windows Native Alternative (If WSL doesn't work)

Install Memurai:
```bash
# Download and run MSI from:
# https://github.com/microsoftarchive/memurai-db/releases

# After installation, start from Services:
# Services → Redis → Start
```

Or from command line:
```bash
redis-server
```
