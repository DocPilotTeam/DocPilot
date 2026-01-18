# DocPilot Agent - Testing & Validation Guide

## Quick Validation (5 minutes)

### 1. Verify Environment Setup
```bash
cd d:\AutoDoc-Backend\docpilot-agent
python validate_startup.py
```

**Expected Output:**
```
Checking environment variables...
✓ Environment variables loaded successfully

Checking Redis connection...
✓ Redis connection OK

Checking Neo4j connection...
✓ Neo4j connection OK

Checking Python dependencies...
✓ All required packages installed

Checking Celery configuration...
✓ Celery configuration valid

Checking GitHub OAuth configuration...
✓ GitHub OAuth configured

✓ All checks passed! Ready to start
```

If any check fails, see [Troubleshooting](#troubleshooting) section below.

---

## Phase 1: Infrastructure Testing

### Test Redis Connection
```bash
# PowerShell
redis-cli ping
```
**Expected**: `PONG`

### Test Neo4j Connection
```bash
# Using Neo4j Browser
# Go to: http://localhost:7474
# Connect with neo4j / password from .env

# Or using cypher-shell
cypher-shell -a bolt://localhost:7687 -u neo4j -p <PASSWORD_FROM_ENV>

# Run test query:
RETURN "Neo4j Connected!" as message;
```

**Expected**: Connection successful, query returns message

### Test Python Imports
```bash
python -c "from backend.celery_config import celery_app; print('Celery imported successfully')"
python -c "from backend.jobs import worker; print('Worker imported successfully')"
python -c "from backend.api import api_routes; print('API routes imported successfully')"
python -c "from backend.api.webhook import verify_github_webhook_signature; print('Webhook imported successfully')"
```

**Expected**: All imports succeed with success messages

---

## Phase 2: Component Testing

### Test 1: Celery Configuration
```bash
# Check Celery can be imported and configured
python -c "
from backend.celery_config import celery_app
print('Celery App:', celery_app)
print('Broker URL:', celery_app.conf.broker_url)
print('Backend URL:', celery_app.conf.result_backend)
"
```

**Expected Output:**
```
Celery App: <Celery ...>
Broker URL: redis://localhost:6379/0
Backend URL: redis://localhost:6379/0
```

### Test 2: Task Registration
```bash
# Verify all tasks are registered
celery -A backend.celery_config inspect registered
```

**Expected Output:**
```
{
  'celery@HOSTNAME': [
    'backend.jobs.worker.clone_repository',
    'backend.jobs.worker.parse_repository',
    'backend.jobs.worker.generate_cypher',
    'backend.jobs.worker.build_knowledge_graph',
    'backend.jobs.worker.generate_documentation_task',
    'backend.jobs.worker.process_repository_pipeline',
    'backend.jobs.worker.cleanup_project'
  ]
}
```

### Test 3: Celery Worker Health
```bash
# Start a Celery worker (in a new terminal)
celery -A backend.celery_config worker -l info

# In another terminal, check worker status
celery -A backend.celery_config inspect ping
```

**Expected Output:**
```
{
  'celery@HOSTNAME': {'ok': 'pong'}
}
```

### Test 4: Redis Connectivity
```bash
# Check Redis info
redis-cli info

# Check memory usage
redis-cli info memory

# Check connected clients
redis-cli client list
```

**Expected**: Redis responds with stats

---

## Phase 3: API Testing

### Start the FastAPI Server
```bash
# Terminal 1: Start FastAPI
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test 3.1: Health Check
```bash
# Test if API is running
curl http://localhost:8000/docs
```

**Expected**: Swagger UI page loads

### Test 3.2: Check Available Tasks
```bash
curl http://localhost:8000/api/tasks
```

**Expected Response:**
```json
{
  "active": 0,
  "scheduled": 0,
  "reserved": 0
}
```

### Test 3.3: Test Webhook Signature Verification
```bash
# Create a test script: test_webhook.py
python test_webhook.py
```

Content of `test_webhook.py`:
```python
import hmac
import hashlib
import json
from backend.core.config import settings

# Create test payload
payload = json.dumps({"test": "data"}).encode()

# Generate signature like GitHub does
signature = hmac.new(
    settings.GITHUB_WEBHOOK_SECRET.encode(),
    payload,
    hashlib.sha256
).hexdigest()

print(f"Payload: {payload}")
print(f"Signature: sha256={signature}")

# Test verification function
from backend.api.webhook import verify_github_webhook_signature
result = verify_github_webhook_signature(payload, f"sha256={signature}")
print(f"Verification result: {result}")
```

**Expected Output:**
```
Payload: b'{"test": "data"}'
Signature: sha256=...
Verification result: True
```

### Test 3.4: Test GitHub OAuth Configuration
```python
# Create: test_github_oauth.py
from backend.auth.github import get_user_repositories
import asyncio

# Note: Replace with actual GitHub token for testing
TOKEN = "github_pat_xxxxx"  # Your GitHub personal access token

async def test():
    try:
        repos = await get_user_repositories(TOKEN)
        print(f"Found {len(repos)} repositories:")
        for repo in repos[:3]:  # Show first 3
            print(f"  - {repo['name']} ({repo['language'] or 'Unknown'})")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
```

**Expected Output:**
```
Found 25 repositories:
  - project-1 (Python)
  - project-2 (JavaScript)
  - project-3 (Java)
```

---

## Phase 4: Task Testing

### Test 4.1: Test Individual Tasks

#### Create test_tasks.py:
```python
from backend.celery_config import celery_app
from backend.jobs.worker import (
    clone_repository,
    parse_repository,
    generate_cypher,
    build_knowledge_graph,
    generate_documentation_task,
    process_repository_pipeline
)
import time

# Make sure Celery worker is running before these tests!

def test_clone_task():
    """Test cloning a repository"""
    print("\n1. Testing clone_repository task...")
    
    # Use a small test repo
    result = clone_repository.delay(
        proj_name="test-clone",
        repo_url="https://github.com/python/cpython.git",  # Public repo
        branch="main",
        github_token=""  # Not needed for public repos
    )
    
    print(f"Task ID: {result.id}")
    print(f"Status: {result.status}")
    
    # Wait for result
    try:
        output = result.get(timeout=60)
        print(f"Result: {output}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_parse_task():
    """Test parsing a repository"""
    print("\n2. Testing parse_repository task...")
    
    result = parse_repository.delay(proj_name="test-clone")
    
    print(f"Task ID: {result.id}")
    
    try:
        output = result.get(timeout=60)
        print(f"Parsed {len(output)} files")
        if output:
            print(f"Sample: {output[0]}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_task_status():
    """Test task status endpoint"""
    print("\n3. Testing task status monitoring...")
    
    result = clone_repository.delay(
        proj_name="test-status",
        repo_url="https://github.com/nodejs/node.git",
        branch="main",
        github_token=""
    )
    
    task_id = result.id
    print(f"Task ID: {task_id}")
    
    # Check status multiple times
    for i in range(5):
        status = celery_app.AsyncResult(task_id).status
        print(f"Check {i+1}: {status}")
        time.sleep(2)
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("DocPilot Task Testing Suite")
    print("=" * 50)
    
    tests = [
        ("Clone Task", test_clone_task),
        ("Parse Task", test_parse_task),
        ("Status Monitoring", test_task_status),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "✓ PASS" if success else "✗ FAIL"))
        except Exception as e:
            results.append((name, f"✗ ERROR: {e}"))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    for name, result in results:
        print(f"{name}: {result}")
```

Run it:
```bash
python test_tasks.py
```

### Test 4.2: Monitor Task Execution
```bash
# Terminal with Celery worker running - Monitor in real-time
celery -A backend.celery_config events

# Or use Flower UI (if running)
# Open browser: http://localhost:5555
```

---

## Phase 5: Full Pipeline Testing

### End-to-End Test Flow

#### Step 1: Start All Services
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A backend.celery_config worker -l info

# Terminal 3: FastAPI
cd backend
uvicorn main:app --reload --port 8000

# Terminal 4 (Optional): Flower Monitoring
celery -A backend.celery_config flower
```

#### Step 2: Test Full Pipeline via API

Create `test_e2e.py`:
```python
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_full_pipeline():
    """Test the complete processing pipeline"""
    
    print("Starting End-to-End Pipeline Test\n")
    
    # 1. Trigger pipeline
    print("1. Triggering repository processing...")
    payload = {
        "proj_name": "test-e2e",
        "repo_url": "https://github.com/microsoft/vscode-python.git",
        "branch": "main",
        "github_token": ""  # Not needed for public repos
    }
    
    response = requests.post(f"{BASE_URL}/api/process-repository", json=payload)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    data = response.json()
    task_id = data.get("task_id")
    print(f"Task ID: {task_id}\n")
    
    # 2. Monitor task progress
    print("2. Monitoring task progress...")
    start_time = time.time()
    timeout = 300  # 5 minutes
    
    statuses_seen = set()
    
    while time.time() - start_time < timeout:
        # Get task status
        status_response = requests.get(f"{BASE_URL}/api/task-status/{task_id}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status not in statuses_seen:
                statuses_seen.add(status)
                print(f"  Status: {status}")
                
                if status_data.get("message"):
                    print(f"  Message: {status_data['message']}")
            
            # Check if completed
            if status == "SUCCESS":
                print(f"\n✓ Pipeline Completed Successfully!")
                print(f"Result: {json.dumps(status_data.get('result'), indent=2)}")
                return True
            
            elif status == "FAILURE":
                print(f"\n✗ Pipeline Failed!")
                print(f"Error: {status_data.get('error')}")
                return False
        
        time.sleep(3)
    
    print("\n✗ Timeout waiting for pipeline completion")
    return False

if __name__ == "__main__":
    try:
        success = test_e2e()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        exit(1)
```

Run it:
```bash
python test_e2e.py
```

**Expected Output:**
```
Starting End-to-End Pipeline Test

1. Triggering repository processing...
Response Status: 200
Task ID: abc123def456

2. Monitoring task progress...
  Status: PENDING
  Status: STARTED
  Status: PROGRESS
  Message: Cloning repository...
  Status: PROGRESS
  Message: Parsing repository...
  Status: PROGRESS
  Message: Generating Cypher...
  Status: PROGRESS
  Message: Building knowledge graph...
  Status: PROGRESS
  Message: Generating documentation...
  Status: SUCCESS

✓ Pipeline Completed Successfully!
```

---

## Phase 6: Webhook Testing

### Test GitHub Webhook

#### 1. Generate Test Webhook
Create `test_webhook_push.py`:
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

response = requests.post(
    "http://localhost:8000/api/webhook",
    json=payload,
    headers=headers
)

print(f"Response Status: {response.status_code}")
print(f"Response: {response.json()}")
```

Run it:
```bash
python test_webhook_push.py
```

**Expected Output:**
```
Response Status: 202
Response: {"status": "accepted", "message": "Push event processed"}
```

#### 2. Verify Task Was Queued
```bash
# Check Celery active tasks
celery -A backend.celery_config inspect active

# Should show a process_repository_pipeline task queued
```

---

## Phase 7: Database Testing

### Verify Neo4j Graph Created

```bash
# Open Neo4j Browser: http://localhost:7474

# Run these queries to verify:

# 1. Count all nodes
MATCH (n) RETURN count(n) as node_count;

# 2. Show node labels
MATCH (n) RETURN distinct labels(n) as node_types, count(*) as count;

# 3. Show relationships
MATCH ()-[r]->() RETURN type(r) as relationship_type, count(*) as count;

# 4. Sample a project's structure
MATCH (p:Project {name: "test-clone"}) 
RETURN p, size((p)-[:CONTAINS]->()) as file_count;

# 5. Find classes in a specific project
MATCH (p:Project {name: "test-clone"})-[:CONTAINS]->(f:File)-[:CONTAINS]->(c:Class)
RETURN c.name as class_name, size((c)-[:HAS_METHOD]->()) as method_count;
```

**Expected**: Nodes and relationships created from parsed repository

---

## Phase 8: Performance Testing

### Load Test Celery Queue

Create `test_load.py`:
```python
from backend.celery_config import celery_app
from backend.jobs.worker import clone_repository
import time

print("Testing Celery queue with 10 concurrent tasks...")

task_ids = []

# Queue 10 tasks
for i in range(10):
    result = clone_repository.delay(
        proj_name=f"test-load-{i}",
        repo_url="https://github.com/jquery/jquery.git",
        branch="main",
        github_token=""
    )
    task_ids.append(result.id)
    print(f"Queued task {i+1}: {result.id}")

# Monitor completion
print("\nMonitoring task completion...")
start = time.time()

while len(task_ids) > 0:
    completed = []
    for task_id in task_ids:
        result = celery_app.AsyncResult(task_id)
        if result.status in ("SUCCESS", "FAILURE"):
            completed.append(task_id)
            print(f"Completed: {task_id} ({result.status})")
    
    for task_id in completed:
        task_ids.remove(task_id)
    
    time.sleep(2)

elapsed = time.time() - start
print(f"\nAll tasks completed in {elapsed:.2f} seconds")
```

---

## Troubleshooting

### Issue 1: Redis Connection Failed
```
Error: ConnectionError: Error 111 connecting to localhost:6379
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server

# On Windows with WSL:
wsl redis-server
```

### Issue 2: Celery Worker Not Starting
```
Error: Cannot connect to amqp://...
```

**Solution:**
```bash
# Verify CELERY_BROKER_URL in .env
echo $CELERY_BROKER_URL

# Check Redis is running and accessible
redis-cli info

# Restart Celery worker with verbose logging
celery -A backend.celery_config worker -l debug
```

### Issue 3: Neo4j Connection Failed
```
Error: Unable to connect to bolt://localhost:7687
```

**Solution:**
```bash
# Check Neo4j status
neo4j status

# Start Neo4j
neo4j start

# Verify credentials
# Username: neo4j
# Password: Check .env neo4j_pass variable
```

### Issue 4: Tasks Stuck in PENDING
```
Status: PENDING (never changes)
```

**Solution:**
```bash
# Verify Celery worker is running
celery -A backend.celery_config inspect ping

# Check Redis memory
redis-cli info memory

# Restart worker
# Ctrl+C to stop, then:
celery -A backend.celery_config worker -l info
```

### Issue 5: GitHub Token Not Working
```
Error: Bad credentials
```

**Solution:**
```bash
# Verify GitHub credentials in .env
# GITHUB_CLIENT_ID: From GitHub OAuth App settings
# GITHUB_CLIENT_SECRET: From GitHub OAuth App settings
# GITHUB_WEBHOOK_SECRET: Generate new one with: 
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Issue 6: Parse Task Failing
```
Error: No module named 'ast' or similar
```

**Solution:**
```bash
# Verify all dependencies installed
pip install -r requirements.txt

# Check imports manually
python -c "from backend.agents.parser.parser_manager import parse_repository_code"
```

---

## Monitoring Checklist

Use this checklist during testing:

- [ ] Redis is running and responsive (`redis-cli ping`)
- [ ] Neo4j is running and accessible
- [ ] Celery worker is running (`celery inspect ping`)
- [ ] FastAPI server is running (`curl localhost:8000/docs`)
- [ ] All imports work (`python validate_startup.py`)
- [ ] At least one task completes successfully
- [ ] Neo4j has nodes from parsed repository
- [ ] Webhook signature verification passes
- [ ] Task status endpoint returns correct status
- [ ] Generated documentation file created

---

## Quick Test Commands Cheatsheet

```bash
# Validate everything
python validate_startup.py

# Test individual components
redis-cli ping
cypher-shell -a bolt://localhost:7687 -u neo4j -p password
celery -A backend.celery_config inspect ping

# Run test suites
python test_tasks.py
python test_e2e.py
python test_webhook_push.py
python test_load.py

# Monitor
celery -A backend.celery_config events
celery -A backend.celery_config inspect active
flower  # Opens http://localhost:5555

# Check logs
celery -A backend.celery_config worker -l info
```

---

## Success Criteria

Your project is working correctly if:

✅ All validation checks pass  
✅ Redis responds to ping  
✅ Neo4j browser loads  
✅ Celery worker is active  
✅ FastAPI Swagger UI loads  
✅ At least one task completes  
✅ Neo4j contains parsed data  
✅ Documentation file is generated  
✅ Webhook accepts requests with valid signature  
✅ No errors in logs  

If all these are true, your project is **fully operational**! 🎉

---

## Next Steps

1. **If all tests pass**: Deploy to staging/production
2. **If tests fail**: Check [Troubleshooting](#troubleshooting) section
3. **For performance tuning**: See [Performance Testing](#phase-8-performance-testing)
4. **For monitoring in production**: Set up Flower UI and logging
