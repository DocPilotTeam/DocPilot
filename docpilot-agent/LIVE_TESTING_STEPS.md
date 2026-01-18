# Live Application Testing - Step by Step

> **Status**: uvicorn server running on http://localhost:8000

## 🎯 Quick Start (Do This Now)

### Step 1: Verify API is Running
Open your browser or terminal:

```bash
# Option 1: Open in browser
http://localhost:8000/docs
# Should show Swagger UI

# Option 2: curl command
curl http://localhost:8000/docs
```

**Expected**: Swagger UI loads with all endpoints listed

---

## 🧪 Phase 1: Basic Health Checks (5 min)

### 1.1 Check Available Tasks
```bash
curl http://localhost:8000/api/tasks
```

**Expected Response**:
```json
{
  "active": 0,
  "scheduled": 0,
  "reserved": 0
}
```

### 1.2 Test Webhook Health
```bash
curl http://localhost:8000/api/webhook -X POST \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=invalid" \
  -d '{"test": "data"}'
```

**Expected**: 
- Status: `401` or `403` (signature verification failed - expected)
- Message: `Invalid webhook signature`

### 1.3 Check All Available Endpoints
```bash
curl http://localhost:8000/openapi.json | python -m json.tool | grep -i "path"
```

**Expected**: Lists all API paths including:
- `/api/process-repository`
- `/api/task-status/{task_id}`
- `/api/tasks`
- `/api/webhook`
- etc.

---

## 🔌 Phase 2: Before Running Tasks - Prerequisites

### Check 1: Is Redis Running?
```bash
redis-cli ping
```
**Expected**: `PONG`

### Check 2: Is Neo4j Running?
```bash
curl http://localhost:7474
```
**Expected**: HTTP 200, Neo4j browser page loads

### Check 3: Is Celery Worker Running?
Open a **NEW terminal** and start the Celery worker:
```bash
# Terminal 2 (New)
cd d:\AutoDoc-Backend\docpilot-agent
myenv\Scripts\celery -A backend.celery_config worker -l info
```

**Expected Output**:
```
-------------- celery@HOSTNAME v5.4.0
---- **** -----
--- * ***  * -- Windows-...
-- * - **** ---
- ** ---------- [config]
- ** ---------- .broker: redis://localhost:6379/0
- ** ---------- .app: backend.celery_config:celery_app
...
[*] Ready to accept tasks!
```

**IMPORTANT**: Keep this terminal running for task tests!

---

## 📝 Phase 3: Test Individual Endpoints (10 min)

### 3.1 Test Process Repository Endpoint

**Create test file**: `test_process_repo.py`

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Test payload
payload = {
    "proj_name": "test-project",
    "repo_url": "https://github.com/jquery/jquery.git",
    "branch": "main",
    "github_token": ""
}

print("1. Sending process-repository request...")
response = requests.post(f"{BASE_URL}/api/process-repository", json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    task_id = response.json().get("task_id")
    print(f"\n✓ Task created successfully!")
    print(f"Task ID: {task_id}")
    print(f"\nNext: Monitor progress with:")
    print(f"  curl http://localhost:8000/api/task-status/{task_id}")
else:
    print(f"\n✗ Error: {response.text}")
```

Run it:
```bash
python test_process_repo.py
```

**Expected Output**:
```json
Status Code: 200
{
  "task_id": "abc123def456xyz",
  "message": "Repository processing started"
}

✓ Task created successfully!
Task ID: abc123def456xyz

Next: Monitor progress with:
  curl http://localhost:8000/api/task-status/abc123def456xyz
```

### 3.2 Monitor Task Progress

Copy the task ID from above and use it here:

```bash
# Replace TASK_ID with actual task ID from above
curl http://localhost:8000/api/task-status/TASK_ID
```

**Expected Output** (changes as task progresses):
```json
{
  "task_id": "abc123def456xyz",
  "status": "PENDING",
  "message": null,
  "result": null,
  "error": null
}
```

Keep running this command every 5-10 seconds to watch progress:
```json
{
  "task_id": "abc123def456xyz",
  "status": "STARTED",
  "message": "Cloning repository...",
  "result": null
}
```

→ Then:
```json
{
  "task_id": "abc123def456xyz",
  "status": "PROGRESS",
  "message": "Parsing repository...",
  "result": null
}
```

→ Then:
```json
{
  "task_id": "abc123def456xyz",
  "status": "SUCCESS",
  "message": "Pipeline completed",
  "result": {
    "project_name": "test-project",
    "files_parsed": 150,
    "cypher_statements": 45,
    "kg_built": true,
    "documentation_generated": true
  }
}
```

---

## 🚀 Phase 4: Full End-to-End Test (15-30 min)

Create `test_e2e_complete.py`:

```python
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_full_pipeline():
    print_section("END-TO-END PIPELINE TEST")
    
    # Step 1: Trigger pipeline
    print_section("STEP 1: Trigger Repository Processing")
    
    payload = {
        "proj_name": "test-e2e",
        "repo_url": "https://github.com/torvalds/linux.git",  # Very large repo for full test
        "branch": "master",
        "github_token": ""
    }
    
    print("Request Payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(f"{BASE_URL}/api/process-repository", json=payload)
    
    if response.status_code != 200:
        print(f"✗ ERROR: {response.text}")
        return False
    
    data = response.json()
    task_id = data["task_id"]
    
    print(f"\n✓ Pipeline triggered!")
    print(f"Task ID: {task_id}")
    print(f"Status: {data['message']}")
    
    # Step 2: Monitor progress
    print_section("STEP 2: Monitor Task Progress")
    
    start_time = time.time()
    timeout = 600  # 10 minutes max
    last_status = None
    statuses_seen = set()
    
    while time.time() - start_time < timeout:
        try:
            status_response = requests.get(f"{BASE_URL}/api/task-status/{task_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data.get("status")
                
                if current_status not in statuses_seen:
                    statuses_seen.add(current_status)
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"[{timestamp}] Status: {current_status}")
                    if status_data.get("message"):
                        print(f"            Message: {status_data['message']}")
                
                # Check if completed
                if current_status == "SUCCESS":
                    print_section("STEP 3: Pipeline Completed Successfully! ✓")
                    print("\nFinal Result:")
                    print(json.dumps(status_data.get("result"), indent=2))
                    return True
                
                elif current_status == "FAILURE":
                    print_section("STEP 3: Pipeline Failed! ✗")
                    print(f"Error: {status_data.get('error')}")
                    return False
        
        except Exception as e:
            print(f"Error checking status: {e}")
        
        time.sleep(5)  # Check every 5 seconds
    
    print(f"\n✗ Timeout after {timeout} seconds")
    return False

def test_active_tasks():
    """Check currently active tasks"""
    print_section("ACTIVE TASKS")
    
    response = requests.get(f"{BASE_URL}/api/tasks")
    data = response.json()
    
    print(f"Active Tasks: {data.get('active', 0)}")
    print(f"Scheduled Tasks: {data.get('scheduled', 0)}")
    print(f"Reserved Tasks: {data.get('reserved', 0)}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  DocPilot Application - Live Testing")
    print("="*60)
    
    # Check active tasks
    test_active_tasks()
    
    # Run full pipeline test
    success = test_full_pipeline()
    
    print_section("SUMMARY")
    if success:
        print("✓ Application is working correctly!")
        print("\nNext steps:")
        print("1. Check generated documentation:")
        print("   cat backend/UserRepos/test-e2e/GENERATED_README.md")
        print("2. Query Neo4j database for created nodes")
        print("3. Test webhook integration (see TESTING_GUIDE.md)")
    else:
        print("✗ Application test failed")
        print("Check the logs in:")
        print("- Terminal running uvicorn: http://localhost:8000")
        print("- Terminal running celery worker")
        print("- Redis logs")
        print("- Neo4j logs")

```

Run it:
```bash
python test_e2e_complete.py
```

---

## 📊 Phase 5: Verify Database Results

After successful pipeline, verify data in Neo4j:

### 5.1 Open Neo4j Browser
```
http://localhost:7474
```

Login with credentials from `.env` file

### 5.2 Run These Queries

**Query 1: Count all nodes**
```cypher
MATCH (n) RETURN count(n) as total_nodes;
```

**Query 2: View node types**
```cypher
MATCH (n) RETURN distinct labels(n) as node_types, count(*) as count;
```

**Query 3: View project structure**
```cypher
MATCH (p:Project {name: "test-e2e"}) 
RETURN p.name as project, 
       size((p)-[:CONTAINS]->()) as file_count;
```

**Query 4: View classes in project**
```cypher
MATCH (p:Project {name: "test-e2e"})-[:CONTAINS]->(f:File)-[:CONTAINS]->(c:Class)
RETURN c.name as class_name, f.name as file_name LIMIT 10;
```

**Expected**: Nodes and relationships from your repository

### 5.3 Check Generated Documentation
```bash
# Check if file exists
dir backend\UserRepos\test-e2e\

# View generated README
type backend\UserRepos\test-e2e\GENERATED_README.md
```

---

## 🔗 Phase 6: Test GitHub OAuth (Optional)

If you have GitHub OAuth credentials configured:

### 6.1 Login Endpoint
Open in browser:
```
http://localhost:8000/auth/login/github
```

**Expected**: Redirects to GitHub OAuth login

### 6.2 After Authorization
Should redirect back with JWT token

### 6.3 Get Repositories
```bash
# Using the token you received
curl http://localhost:8000/auth/github/repos \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected**: List of your GitHub repositories

---

## 🪝 Phase 7: Test Webhook (Optional)

Create `test_webhook_trigger.py`:

```python
import requests
import json
import hmac
import hashlib
from backend.core.config import settings

# Simulate GitHub push event
payload = {
    "action": "opened",
    "repository": {
        "name": "test-repo",
        "url": "https://github.com/user/test-repo",
        "full_name": "user/test-repo"
    },
    "push": {
        "commits": [
            {
                "id": "abc123",
                "message": "Test commit"
            }
        ]
    },
    "ref": "refs/heads/main"
}

payload_body = json.dumps(payload).encode()

# Create GitHub signature
signature = hmac.new(
    settings.GITHUB_WEBHOOK_SECRET.encode(),
    payload_body,
    hashlib.sha256
).hexdigest()

# Send to webhook
headers = {
    "X-GitHub-Event": "push",
    "X-Hub-Signature-256": f"sha256={signature}",
    "Content-Type": "application/json"
}

print("Sending webhook request...")
response = requests.post(
    "http://localhost:8000/api/webhook",
    json=payload,
    headers=headers
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 202:
    print("\n✓ Webhook accepted and processing started!")
else:
    print("\n✗ Webhook failed")
```

Run it:
```bash
python test_webhook_trigger.py
```

---

## ✅ Complete Testing Checklist

Run through this checklist to verify everything works:

- [ ] **API Health**: `curl http://localhost:8000/docs` → Swagger UI loads
- [ ] **Tasks Endpoint**: `curl http://localhost:8000/api/tasks` → Returns JSON
- [ ] **Celery Worker**: Running and showing "[*] Ready to accept tasks!"
- [ ] **Redis**: `redis-cli ping` → Returns PONG
- [ ] **Neo4j**: Browser loads at `http://localhost:7474`
- [ ] **Process Repository**: Task created with task_id
- [ ] **Task Status**: Status changes from PENDING → STARTED → SUCCESS
- [ ] **Database**: Neo4j has nodes created
- [ ] **Documentation**: Generated README file exists
- [ ] **Webhook**: Accepts valid signature (optional)
- [ ] **No Errors**: Check terminal logs for any exceptions

---

## 🔍 Monitoring & Debugging

### Real-time Logs
**Terminal 1 (uvicorn)**: Shows API requests
**Terminal 2 (Celery Worker)**: Shows task execution

### Flower Dashboard (Optional)
Open new terminal:
```bash
myenv\Scripts\celery -A backend.celery_config flower
```

Access: `http://localhost:5555`

Shows:
- Active workers
- Task history
- Task execution times
- Errors

### Check Logs
```bash
# Celery tasks
celery -A backend.celery_config inspect active

# Redis info
redis-cli info

# Neo4j status
curl http://localhost:7474/db/neo4j/info
```

---

## 🚨 Troubleshooting Quick Guide

### Issue: "Task stuck in PENDING"
```bash
# Check Celery worker is running
celery -A backend.celery_config inspect ping

# Restart worker if needed
# Ctrl+C in Celery terminal, then:
myenv\Scripts\celery -A backend.celery_config worker -l info
```

### Issue: "Neo4j connection error"
```bash
# Check Neo4j is running
curl http://localhost:7474

# Verify credentials in .env
# Check neo4j_url and neo4j_pass
```

### Issue: "Redis connection error"
```bash
# Check Redis is running
redis-cli ping

# Start Redis if needed
redis-server
```

### Issue: "Task returns error"
```bash
# Check Celery worker logs for full error
# Look at uvicorn logs for API errors
# Check .env variables are set correctly
```

---

## 📈 Success Indicators

Your application is **fully working** when:

✅ All health checks pass  
✅ Task processes from PENDING → SUCCESS  
✅ Neo4j has nodes created  
✅ GENERATED_README.md file exists  
✅ Status endpoint returns real-time updates  
✅ No errors in logs  

**Congratulations! Your DocPilot application is production-ready!** 🎉
