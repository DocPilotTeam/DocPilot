# Celery Integration Setup Guide

This guide explains how to set up and run the Celery task queue system for DocPilot Agent.

## Overview

DocPilot now uses **Celery** with **Redis** as the message broker to process repositories asynchronously. The complete workflow is:

```
GitHub OAuth Login → User selects repository → Webhook/API triggers
       ↓
  Celery Task Queue
       ↓
  Clone → Parse → Cypher → Build KG → Generate Docs
```

## Prerequisites

### 1. Redis Server
Required for Celery message broker.

**Windows:**
```bash
# Using WSL (recommended)
wsl sudo apt-get install redis-server
wsl redis-server

# Or download from: https://github.com/microsoftarchive/redis/releases
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

### 2. Python Dependencies
Install all packages including Celery:
```bash
pip install -r requirements.txt
```

## Environment Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and configure:
```
GITHUB_CLIENT_ID=your_id
GITHUB_CLIENT_SECRET=your_secret
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback
GITHUB_WEBHOOK_SECRET=your_webhook_secret

neo4j_url=bolt://localhost:7687
neo4j_pass=your_password

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

OPENAI_API_KEY=your_key
gemini_api_key=your_key

JWT_SECRET=your_secret_key
```

## Starting the Application

### Option 1: All-in-One Script (Recommended)

**Windows:**
```bash
start_all.bat
```
This will open FastAPI and Celery Worker in separate terminal windows.

**Linux/macOS:**
```bash
bash start_all.sh
```

### Option 2: Start Services Separately

**Terminal 1 - FastAPI Server:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Celery Worker:**
```bash
celery -A backend.celery_config worker --loglevel=info --concurrency=4
```

**Terminal 3 - Celery Beat (optional, for periodic tasks):**
```bash
celery -A backend.celery_config beat --loglevel=info
```

**Terminal 4 - Flower Monitoring UI (optional):**
```bash
flower -A backend.celery_config --port=5555
```

Or use the provided scripts:
- `start_worker.bat` - Start Celery Worker
- `start_beat.bat` - Start Celery Beat Scheduler
- `start_flower.bat` - Start Flower UI

## API Endpoints

### Authentication
```
GET /auth/login/github
→ Redirects to GitHub OAuth

GET /auth/github/callback?code=...
→ Returns JWT token and list of user's repositories
```

### Repository Processing (Async)

**Full Pipeline (Recommended):**
```
POST /api/process-repository
{
  "proj_name": "my-repo",
  "repo_url": "https://github.com/user/my-repo",
  "branch": "main",
  "github_token": "ghp_..."
}
→ Returns: {"status": "processing", "task_id": "abc123"}
```

**Individual Steps:**
```
POST /api/clone-repo-async
POST /api/parse-repo-async
POST /api/generate-docs-async
```

### Task Monitoring
```
GET /api/task-status/{task_id}
→ Returns: {"task_id": "abc123", "status": "PENDING|STARTED|SUCCESS|FAILURE", "result": {...}}

GET /api/tasks
→ Returns: {"active": {...}, "scheduled": {...}, "reserved": {...}}
```

## GitHub Webhook Setup

1. Go to your GitHub repository
2. Settings → Webhooks → Add webhook
3. Configure:
   - **Payload URL**: `https://yourdomain.com/api/webhook`
   - **Content type**: `application/json`
   - **Secret**: Your `GITHUB_WEBHOOK_SECRET` from `.env`
   - **Events**: Select "Pushes"

4. The webhook will automatically trigger documentation regeneration on every push!

## Monitoring Tasks

### Flower Web UI
Visit `http://localhost:5555` to monitor:
- Active tasks
- Task history
- Worker status
- Task execution times
- Failures and retries

### Command Line
```bash
# View active tasks
celery -A backend.celery_config inspect active

# View scheduled tasks
celery -A backend.celery_config inspect scheduled

# View worker stats
celery -A backend.celery_config inspect stats

# View registered tasks
celery -A backend.celery_config inspect registered
```

## Pipeline Architecture

### 1. Clone Repository
```python
clone_repository(proj_name, repo_url, branch, github_token)
```
- Clones or updates repository from GitHub
- Stores in `UserRepos/{proj_name}/`

### 2. Parse Code
```python
parse_repository(proj_name)
```
- Walks through all code files
- Parses using language-specific parsers
- Returns AST structure

### 3. Generate Cypher
```python
generate_cypher(proj_name, parsed_data)
```
- Sends AST to Gemini AI
- Generates Neo4j Cypher statements
- Returns list of Cypher queries

### 4. Build Knowledge Graph
```python
build_knowledge_graph(proj_name, cypher_statements)
```
- Executes Cypher queries in Neo4j
- Creates nodes: File, Class, Method
- Creates relationships: CONTAINS_CLASS, HAS_METHOD, CALLS

### 5. Generate Documentation
```python
generate_documentation_task(proj_name)
```
- Queries Neo4j knowledge graph
- Sends structured data to LLM
- Generates professional README.md
- Saves to `UserRepos/{proj_name}/GENERATED_README.md`

## Task Workflow Example

```
User selects "my-repo" from GitHub auth callback
          ↓
POST /api/process-repository
          ↓
Celery Queue (Redis)
          ↓
Worker picks up task
          ↓
[Clone] → task returned: {progress: 25%}
[Parse] → task returned: {progress: 50%}
[Cypher] → task returned: {progress: 75%}
[KG] → task returned: {progress: 87%}
[Docs] → task returned: {progress: 100%}
          ↓
Task completed: GENERATED_README.md created
          ↓
Frontend polls /api/task-status/{task_id}
          ↓
Returns: {status: "SUCCESS", result: {documentation: "..."}}
```

## Error Handling

### Task Failures
If a task fails:
1. Check Celery Worker logs
2. Use Flower UI to inspect failure details
3. View `/api/task-status/{task_id}` for error message
4. Re-trigger task after fixing issue

### Common Issues

**Redis connection refused:**
```
Error: ConnectionError: Error 111 connecting to localhost:6379
Fix: Start Redis server first
```

**No module named backend.celery_config:**
```
Error: ModuleNotFoundError
Fix: Run command from project root directory
```

**GitHub token invalid:**
```
Error: git@github.com: Permission denied
Fix: Verify GITHUB_TOKEN is valid and has repo access
```

## Performance Tuning

### Worker Concurrency
```bash
# Default 4 workers
celery -A backend.celery_config worker --concurrency=8

# Solo pool (single worker, better for debugging)
celery -A backend.celery_config worker --pool=solo
```

### Task Timeouts
Edit `.celery_config.py`:
```python
task_time_limit=30 * 60,  # 30 minutes hard limit
task_soft_time_limit=25 * 60,  # 25 minutes soft limit
```

### Result Backend
Redis persists results for 1 hour by default:
```python
result_expires=3600  # Change as needed
```

## Production Deployment

### Requirements
1. Use proper web server: Gunicorn, Uvicorn
2. Use Supervisord or systemd for process management
3. Configure Redis persistence and backups
4. Set up proper logging and monitoring
5. Use strong JWT_SECRET
6. Enable HTTPS for webhooks

### Example Systemd Service

Create `/etc/systemd/system/docpilot-worker.service`:
```ini
[Unit]
Description=DocPilot Celery Worker
After=network.target redis-server.service

[Service]
Type=forking
User=docpilot
WorkingDirectory=/opt/docpilot-agent
ExecStart=/opt/docpilot-agent/myenv/bin/celery -A backend.celery_config worker --loglevel=info --logfile=/var/log/docpilot/celery.log --pidfile=/var/run/celery.pid

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable docpilot-worker
sudo systemctl start docpilot-worker
```

## Troubleshooting

### Check Redis
```bash
redis-cli ping
# Should return: PONG
```

### Check Celery
```bash
celery -A backend.celery_config inspect ping
# Should return worker response
```

### View Task Details
```python
from backend.celery_config import app

result = app.AsyncResult('task-id-here')
print(result.status)
print(result.result)
print(result.traceback)  # If failed
```

## Documentation Links

- [Celery Documentation](https://docs.celeryproject.io/)
- [Flower GitHub](https://github.com/mher/flower)
- [Redis Documentation](https://redis.io/documentation)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

## Support

For issues or questions:
1. Check Celery logs
2. Use Flower UI for task inspection
3. Review error messages in `/api/task-status/{task_id}`
4. Check Neo4j connection
5. Verify GitHub token permissions
