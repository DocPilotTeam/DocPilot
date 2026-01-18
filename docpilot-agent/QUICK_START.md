# Quick Start Guide - DocPilot Agent with Celery

## 5-Minute Setup

### Step 1: Prerequisites
```bash
# Install Redis
# macOS:
brew install redis
brew services start redis

# Linux:
sudo apt-get install redis-server
sudo systemctl start redis-server

# Windows: Use WSL or download from https://github.com/microsoftarchive/redis/releases
```

### Step 2: Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Validate Setup
```bash
python validate_startup.py
```

### Step 5: Start Application

**Windows:**
```bash
start_all.bat
```

**Linux/macOS:**
```bash
bash start_all.sh
```

This starts:
- FastAPI Server on http://localhost:8000
- Celery Worker
- Flower monitoring on http://localhost:5555 (optional)

## How It Works

### 1. User Authentication
```
User clicks "Login with GitHub"
→ https://localhost:8000/auth/login/github
→ GitHub OAuth redirect
→ Returns JWT token + list of user's repositories
```

### 2. User Selects Repository
```
Frontend gets list of repos from OAuth response
→ User clicks on repo "my-project"
→ Frontend calls POST /api/process-repository
```

### 3. Async Processing Starts
```
POST /api/process-repository
{
  "proj_name": "my-project",
  "repo_url": "https://github.com/user/my-project",
  "branch": "main",
  "github_token": "ghp_..."
}
↓
Returns: {"status": "processing", "task_id": "abc123def456"}
```

### 4. Pipeline Executes
```
Celery Worker processes task:
  1. Clone repository (25% progress)
  2. Parse code files (50% progress)
  3. Generate Cypher (75% progress)
  4. Build knowledge graph (87% progress)
  5. Generate documentation (100% progress)
```

### 5. Monitor Progress
```
Frontend polls GET /api/task-status/abc123def456
→ {"status": "STARTED", "message": "Parsing files..."}
→ {"status": "SUCCESS", "result": {documentation: "..."}}
```

### 6. GitHub Webhook (Optional)
```
Any push to repository
→ GitHub sends webhook to /api/webhook
→ Automatically triggers new documentation generation
→ Documentation stays up-to-date!
```

## Example Usage

### Using cURL

**Authenticate:**
```bash
curl -L "http://localhost:8000/auth/login/github"
# Follow redirect to GitHub, get token and repo list
```

**Process Repository:**
```bash
curl -X POST "http://localhost:8000/api/process-repository" \
  -H "Content-Type: application/json" \
  -d '{
    "proj_name": "docpilot-agent",
    "repo_url": "https://github.com/user/docpilot-agent",
    "branch": "main",
    "github_token": "ghp_your_token_here"
  }'
# Returns: {"status": "processing", "task_id": "task-123"}
```

**Check Status:**
```bash
curl "http://localhost:8000/api/task-status/task-123"
# Returns: {"status": "SUCCESS", "result": {...}}
```

## File Locations

After processing, files are stored at:
```
UserRepos/
├── my-project/
│   ├── src/
│   ├── .git/
│   ├── GENERATED_README.md  ← Generated documentation
│   └── ...
```

## Monitoring

### Flower UI
Visit `http://localhost:5555`
- See all active tasks
- Monitor worker status
- View task execution times
- Check failed tasks

### Terminal
```bash
# View active tasks
celery -A backend.celery_config inspect active

# View task stats
celery -A backend.celery_config inspect stats

# Get Celery stats
celery -A backend.celery_config inspect registered
```

## Database Schema

### Neo4j Knowledge Graph
```
File {filePath, project}
├─ CONTAINS_CLASS → Class {name, filePath, project}
│  └─ HAS_METHOD → Method {name, parentClass, filePath, project}
│     └─ CALLS → Method {...}
└─ CONTAINS_METHOD → Method {...}
```

Query example:
```cypher
// Find all methods in a class
MATCH (c:Class {name: "MyClass", project: "my-project"})
-[:HAS_METHOD]->(m:Method)
RETURN m
```

## API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login/github` | GET | Initiate GitHub OAuth |
| `/auth/github/callback` | GET | GitHub OAuth callback |
| `/api/process-repository` | POST | Start full pipeline |
| `/api/clone-repo-async` | POST | Clone only |
| `/api/parse-repo-async` | POST | Parse only |
| `/api/generate-docs-async` | POST | Generate docs only |
| `/api/task-status/{task_id}` | GET | Check task status |
| `/api/tasks` | GET | View all tasks |
| `/api/webhook` | POST | GitHub webhook receiver |

## Troubleshooting

### Redis Not Running
```
Error: ConnectionError connecting to localhost:6379
Fix: Start Redis first
```

### Celery Worker Not Picking Tasks
```
Error: No workers available
Fix: Start worker: celery -A backend.celery_config worker --loglevel=info
```

### Neo4j Connection Failed
```
Error: Failed to establish connection
Fix: Check neo4j_url and neo4j_pass in .env
```

### GitHub Token Invalid
```
Error: Authentication failed
Fix: Ensure github_token has 'repo' scope and is valid
```

## Next Steps

1. **Frontend Integration**: Connect your React/Vue frontend to APIs
2. **Webhook Setup**: Configure GitHub webhook in repository settings
3. **Production**: Deploy with Docker, configure monitoring
4. **Customization**: Modify parsers for more languages
5. **Performance**: Tune Celery workers for your system

## Environment Variables Explained

```
# GitHub OAuth - Get from https://github.com/settings/developers
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback

# Webhook Security
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Neo4j Database
neo4j_url=bolt://localhost:7687
neo4j_pass=your_neo4j_password

# Redis & Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# LLM APIs
OPENAI_API_KEY=sk-...  # OpenRouter
gemini_api_key=...      # Google Gemini

# Security
JWT_SECRET=your_secret_key_change_this
```

## Common Workflows

### Weekly Documentation Update
```bash
# Via GitHub Webhook: Every push auto-updates docs
# No manual action needed!
```

### Manual Update
```bash
POST /api/process-repository with repo details
```

### Check Generated Docs
```bash
# Located at:
UserRepos/{proj_name}/GENERATED_README.md
```

### Monitor Long-Running Task
```bash
# For large repositories:
GET /api/task-status/{task_id}  # Poll every 5 seconds
# Will show progress through each pipeline stage
```

## Performance Tips

1. **More Workers**: For large repos, increase concurrency:
   ```bash
   celery -A backend.celery_config worker --concurrency=8
   ```

2. **Skip Directories**: Parsers skip: `.git`, `node_modules`, `__pycache__`, `build`, `dist`

3. **Large Repos**: May take 2-5 minutes, keep polling task status

4. **Redis Optimization**: Use Redis persistence for production

## Security Considerations

⚠️ **Before Production:**
- Change `JWT_SECRET` in .env
- Use HTTPS for webhook
- Validate GitHub webhook signatures ✓ (already implemented)
- Store GitHub tokens securely
- Enable Redis authentication
- Use environment-specific configs

## Support & Documentation

- Full setup guide: See `CELERY_SETUP.md`
- API documentation: http://localhost:8000/docs (Swagger UI)
- Celery docs: https://docs.celeryproject.io/
- GitHub Webhooks: https://docs.github.com/webhooks

---

**Ready to go!** Start with `start_all.bat` (Windows) or `bash start_all.sh` (Linux/macOS)
