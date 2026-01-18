# Complete Startup Instructions for Windows

## 🎯 What You Need Running

Your application needs **3 services** running simultaneously:

1. **Redis** - Message broker (queues tasks)
2. **Celery Worker** - Processes tasks
3. **FastAPI** - Web API server
4. **(Optional) Neo4j** - Knowledge graph database

---

## 📋 Prerequisites Check

Before starting, verify you have these installed:

```bash
# Check Python
python --version
# Expected: Python 3.8+

# Check Redis (if not installed, follow REDIS_WINDOWS_SETUP.md)
wsl redis-cli ping
# Expected: PONG

# Check Neo4j is running
curl http://localhost:7474
# Expected: 200 OK
```

---

## 🚀 Complete Startup (Step by Step)

### Step 1: Open Terminal 1 - Start Redis

```bash
# PowerShell or Command Prompt
wsl redis-server
```

**Expected Output:**
```
           .;lllll;.
        .;;;;;;;;;;;;;;;.
      .;;               ;;.
    .;                    ;.
   ;;                      ;;
  .;                        ;.
  ;;  oO0OOo.  .oO0OOo.     ;;
  ;;  O  d  O  O  d  O      ;;
  ;;  O  d  O  O  d  O      ;;
  .;  oO0OOo.  .oO0OOo.    ;.
   ;;                      ;;
    .;                    ;.
      .;;               ;;.
        .;;;;;;;;;;;;;;;.
           .;lllll;.

        Redis 7.0.0 (compatible)
   
     * Ready to accept connections
```

**⚠️ IMPORTANT**: Keep this terminal open! It's running Redis.

---

### Step 2: Open Terminal 2 - Start Celery Worker

Open a **NEW** PowerShell/Command Prompt window:

```bash
# Navigate to project
cd d:\AutoDoc-Backend\docpilot-agent

# Start Celery worker
myenv\Scripts\celery -A backend.celery_config worker -l info
```

**Expected Output:**
```
-------------- celery@YOUR-PC v5.4.0 (opalescent)
---- **** -----
--- * ***  * -- Windows
-- * - **** ---
- ** ---------- [config]
- ** ---------- .broker: redis://localhost:6379/0
- ** ---------- .app: backend.celery_config:celery_app
- ** ---------- .logfile: [stderr]@...
- ** ---------- [queues]
- ** ---------- .celery: exchange:celery (direct) key:celery

 ... more output ...

[*] Ready to accept tasks!
```

**⚠️ IMPORTANT**: Keep this terminal open! It's processing tasks.

---

### Step 3: Open Terminal 3 - Start FastAPI

Open a **NEW** PowerShell/Command Prompt window:

```bash
# Navigate to backend
cd d:\AutoDoc-Backend\docpilot-agent\backend

# Start FastAPI
uvicorn main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete
```

**✓ Server is ready!**

---

### Step 4: Verify All Services Are Running

Open a **NEW** PowerShell/Command Prompt window:

```bash
# Test 1: Redis
wsl redis-cli ping
# Expected: PONG

# Test 2: Celery
myenv\Scripts\celery -A backend.celery_config inspect ping
# Expected: celery@...: ok pong

# Test 3: FastAPI
curl http://localhost:8000/api/tasks
# Expected: {"active": 0, "scheduled": 0, "reserved": 0}
```

---

## ✅ Quick Terminal Summary

You should now have these windows open:

| # | Name | Command | Status |
|----|------|---------|--------|
| 1 | Redis | `wsl redis-server` | Running (keep open) |
| 2 | Celery | `celery -A backend.celery_config worker -l info` | Running (keep open) |
| 3 | FastAPI | `uvicorn main:app --reload --port 8000` | Running ✓ |
| 4 | Testing | NEW terminal for testing | Ready to use |

---

## 🧪 Now Test Your Application

In Terminal 4 (or new terminal):

### Test 1: Check API
```bash
curl http://localhost:8000/docs
```
Should load Swagger UI

### Test 2: Process a Repository
```bash
curl -X POST http://localhost:8000/api/process-repository ^
  -H "Content-Type: application/json" ^
  -d "{\"proj_name\": \"test-jquery\", \"repo_url\": \"https://github.com/jquery/jquery.git\", \"branch\": \"main\", \"github_token\": \"\"}"
```

**Expected Response:**
```json
{
  "task_id": "abc123xyz789",
  "message": "Repository processing started"
}
```

### Test 3: Check Task Status
```bash
curl http://localhost:8000/api/task-status/abc123xyz789
```

Watch the status change as you repeat this command:
```json
{
  "status": "PENDING",
  "message": null
}
```

Then:
```json
{
  "status": "STARTED",
  "message": "Cloning repository..."
}
```

Then:
```json
{
  "status": "SUCCESS",
  "result": {...}
}
```

---

## 🔍 What to Watch For

### In Redis Terminal (Terminal 1)
- Should see connection messages
- No errors

### In Celery Terminal (Terminal 2)
- Should see `[*] Ready to accept tasks!`
- When tasks run, you'll see:
  ```
  [2025-01-17 10:30:15,123: INFO/MainProcess] Task backend.jobs.worker.clone_repository[...] ...
  [2025-01-17 10:30:16,456: INFO/MainProcess] Task backend.jobs.worker.parse_repository[...] ...
  ```

### In FastAPI Terminal (Terminal 3)
- Should see `Started server process`
- When API requests come in:
  ```
  INFO:     POST /api/process-repository HTTP/1.1" 200 OK
  ```

---

## 📊 Monitoring (Optional)

### Option 1: Flower Dashboard
In Terminal 4:
```bash
myenv\Scripts\celery -A backend.celery_config flower
```

Open: http://localhost:5555

See live task updates!

### Option 2: Task Status via API
```bash
# In Terminal 4
curl http://localhost:8000/api/tasks
# Shows active, scheduled, reserved tasks
```

---

## 🛑 Stopping Everything

When done testing:

1. Terminal 1 (Redis): Press `Ctrl+C`
2. Terminal 2 (Celery): Press `Ctrl+C`
3. Terminal 3 (FastAPI): Press `Ctrl+C`
4. Close all windows

---

## 🚨 Troubleshooting

### Issue: "Can't connect to Redis"
```
Error: Error 10061 connecting to localhost:6379
```
**Solution:** Make sure Terminal 1 is running `wsl redis-server`

### Issue: "Celery worker not starting"
**Solution:** Check Terminal 1 - Redis must be running first

### Issue: "FastAPI port already in use"
```
Error: Address already in use
```
**Solution:** 
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Or use different port:
uvicorn main:app --port 8001
```

### Issue: "Module not found" errors
**Solution:** Make sure you're in the virtual environment:
```bash
# Activate venv
myenv\Scripts\activate

# Then run commands
```

---

## 🎯 Complete Workflow Example

```bash
# Terminal 1: Start Redis
wsl redis-server
# Expected: "Ready to accept connections"

# Terminal 2: Start Celery
cd d:\AutoDoc-Backend\docpilot-agent
myenv\Scripts\celery -A backend.celery_config worker -l info
# Expected: "[*] Ready to accept tasks!"

# Terminal 3: Start FastAPI
cd d:\AutoDoc-Backend\docpilot-agent\backend
uvicorn main:app --reload --port 8000
# Expected: "Uvicorn running on http://0.0.0.0:8000"

# Terminal 4: Test
cd d:\AutoDoc-Backend\docpilot-agent

# 4a: Process repository
curl -X POST http://localhost:8000/api/process-repository ^
  -H "Content-Type: application/json" ^
  -d "{\"proj_name\": \"test-jquery\", \"repo_url\": \"https://github.com/jquery/jquery.git\", \"branch\": \"main\", \"github_token\": \"\"}"
# Copy task_id from response

# 4b: Check status (repeat every 10 seconds)
curl http://localhost:8000/api/task-status/YOUR_TASK_ID_HERE

# 4c: When status is SUCCESS, check results
type backend\UserRepos\test-jquery\GENERATED_README.md
```

---

## ✨ Success Indicators

If you see all of this, you're good to go:

- ✅ Terminal 1: Redis showing "Ready to accept connections"
- ✅ Terminal 2: Celery showing "[*] Ready to accept tasks!"
- ✅ Terminal 3: FastAPI showing "Uvicorn running"
- ✅ Terminal 4: `curl http://localhost:8000/docs` works
- ✅ Task status changes from PENDING → SUCCESS
- ✅ Generated README file is created
- ✅ No errors in any terminal

**Your DocPilot application is fully functional!** 🎉
