# DocPilot Agent - Deployment Checklist

## Pre-Deployment Verification

### ✅ System Requirements
- [ ] Redis 6.0+ installed and running
- [ ] Neo4j database installed and running
- [ ] Python 3.8+ installed
- [ ] Git installed
- [ ] 2GB+ RAM available
- [ ] Network access to GitHub, OpenAI, Google Gemini

### ✅ Environment Configuration
- [ ] `.env` file created from `.env.example`
- [ ] GitHub OAuth credentials configured:
  - [ ] GITHUB_CLIENT_ID set
  - [ ] GITHUB_CLIENT_SECRET set
  - [ ] GITHUB_REDIRECT_URI set
  - [ ] GITHUB_WEBHOOK_SECRET set
- [ ] Neo4j credentials configured:
  - [ ] neo4j_url set
  - [ ] neo4j_pass set
- [ ] Redis URL configured:
  - [ ] CELERY_BROKER_URL set (redis://...)
  - [ ] CELERY_RESULT_BACKEND set (redis://...)
- [ ] API keys configured:
  - [ ] OPENAI_API_KEY set
  - [ ] gemini_api_key set
- [ ] JWT secret changed from default "magic"

### ✅ Dependencies
- [ ] `pip install -r requirements.txt` completed successfully
- [ ] No import errors when starting Python
- [ ] All packages available: celery, redis, neo4j, fastapi, uvicorn

### ✅ Validation
- [ ] `python validate_startup.py` passes all checks
  - [ ] Environment variables OK
  - [ ] Redis connection OK
  - [ ] Neo4j connection OK
  - [ ] Python dependencies OK
  - [ ] Celery configuration OK
  - [ ] GitHub OAuth configured OK

### ✅ GitHub OAuth Setup
- [ ] Created OAuth App at https://github.com/settings/developers
- [ ] Authorization callback URL matches GITHUB_REDIRECT_URI
- [ ] Webhook secret generated and stored in GITHUB_WEBHOOK_SECRET
- [ ] Repository webhook will be configured after user selection

### ✅ Code Review
- [ ] No syntax errors in modified/created files
- [ ] All imports correctly configured
- [ ] Task chains properly defined
- [ ] Error handling in place
- [ ] Logging configured

### ✅ Database Setup
- [ ] Neo4j database created and empty
- [ ] Initial user database schema ready (if using Supabase)
- [ ] Connection credentials verified

### ✅ Startup Scripts
- [ ] `start_all.bat` (Windows) - Exists and executable
- [ ] `start_all.sh` (Linux/macOS) - Exists and executable
- [ ] `start_worker.bat` / `start_worker.sh` - Exists
- [ ] `start_flower.bat` / `start_flower.sh` - Exists (optional)

## Deployment Steps

### Step 1: Infrastructure Setup
```bash
# 1. Start Redis
redis-server  # or brew services start redis (macOS)

# 2. Verify Redis
redis-cli ping
# Expected: PONG

# 3. Start Neo4j
neo4j start

# 4. Verify Neo4j
# Connect to http://localhost:7474 (default)
```

### Step 2: Environment Setup
```bash
# 1. Clone/prepare repository
git clone <your-repo>
cd docpilot-agent

# 2. Create .env file
cp .env.example .env

# 3. Configure .env with all required values
# Use your favorite editor to fill in credentials
```

### Step 3: Validate Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run validation
python validate_startup.py

# 3. Verify all checks pass
# Should see: "✓ All checks passed! Ready to start"
```

### Step 4: Start Services
```bash
# Windows:
start_all.bat

# Linux/macOS:
bash start_all.sh
```

This will start:
- FastAPI on http://localhost:8000
- Celery Worker (background)
- Optional: Flower UI on http://localhost:5555

### Step 5: Verify Services
```bash
# Check FastAPI
curl http://localhost:8000/docs
# Should return Swagger UI

# Check Celery Worker
celery -A backend.celery_config inspect active
# Should return worker status

# Check Redis
redis-cli info
# Should return Redis stats
```

## First Run Workflow

1. **Start Application**
   ```bash
   start_all.bat  # or start_all.sh
   ```

2. **User Login**
   - User visits http://localhost:3000
   - Clicks "Login with GitHub"
   - Redirected to GitHub OAuth
   - Authorizes application
   - Receives JWT token + list of repositories

3. **User Selects Repository**
   - Chooses "my-project" from list
   - Frontend calls: POST /api/process-repository

4. **Monitor Progress**
   - Frontend polls: GET /api/task-status/{task_id}
   - Shows progress: Cloning → Parsing → Building KG → Generating Docs

5. **View Results**
   - Documentation generated at: UserRepos/my-project/GENERATED_README.md
   - Can also view via API: GET /api/task-status/{task_id}

6. **Setup Webhook (Optional)**
   - Go to GitHub repo settings
   - Add Webhook: https://yourdomain.com/api/webhook
   - Secret: Value from GITHUB_WEBHOOK_SECRET
   - Select "Pushes" event
   - From now on, docs auto-regenerate on push!

## Production Checklist

### Security
- [ ] JWT_SECRET changed from "magic"
- [ ] GitHub credentials not in code (only .env)
- [ ] Redis password set (if applicable)
- [ ] Neo4j authentication enabled
- [ ] HTTPS enabled for webhook
- [ ] Webhook secret strong and random
- [ ] Environment variables not logged
- [ ] Database backups configured

### Performance
- [ ] Celery workers: 4+ for production
- [ ] Redis persistence enabled
- [ ] Neo4j indexes optimized
- [ ] Task timeouts configured appropriately
- [ ] Rate limiting considered
- [ ] Caching strategy in place

### Monitoring
- [ ] Flower UI password protected (if exposed)
- [ ] Logging to file configured
- [ ] Error alerts set up
- [ ] Redis memory limits set
- [ ] Neo4j storage monitored
- [ ] Worker health checks

### Maintenance
- [ ] Backup schedule for Neo4j
- [ ] Redis persistence strategy
- [ ] Log rotation configured
- [ ] Old repositories cleanup plan
- [ ] Version control for .env backups
- [ ] Disaster recovery plan

## Troubleshooting Guide

### Issue: "ConnectionError: Error 111 connecting to localhost:6379"
**Cause**: Redis not running
**Fix**: 
```bash
redis-server  # Start Redis
# or
brew services start redis  # macOS
```

### Issue: "ModuleNotFoundError: No module named 'celery'"
**Cause**: Dependencies not installed
**Fix**:
```bash
pip install -r requirements.txt
```

### Issue: "neo4j.exceptions.ServiceUnavailable: Unable to connect"
**Cause**: Neo4j not running or wrong credentials
**Fix**:
1. Verify Neo4j running: `neo4j status`
2. Check credentials in .env
3. Verify neo4j_url and neo4j_pass

### Issue: "GitHub token exchange failed"
**Cause**: Invalid OAuth credentials
**Fix**:
1. Verify GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env
2. Check GitHub OAuth App settings
3. Verify callback URL matches exactly

### Issue: Celery worker not processing tasks
**Cause**: Worker not started
**Fix**:
```bash
celery -A backend.celery_config worker --loglevel=info
```

### Issue: Tasks stuck in PENDING state
**Cause**: Redis connection issue
**Fix**:
1. Check CELERY_BROKER_URL
2. Verify Redis running: `redis-cli ping`
3. Restart worker: `Ctrl+C` and start again

## Monitoring Commands

### Celery Tasks
```bash
# View active tasks
celery -A backend.celery_config inspect active

# View registered tasks
celery -A backend.celery_config inspect registered

# View worker stats
celery -A backend.celery_config inspect stats

# View worker registered tasks
celery -A backend.celery_config inspect registered

# Purge all pending tasks (CAREFUL!)
celery -A backend.celery_config purge
```

### Redis
```bash
# Check connection
redis-cli ping

# View stats
redis-cli info

# View memory usage
redis-cli info memory

# Monitor commands in real-time
redis-cli monitor
```

### Neo4j
```bash
# Check connectivity
# In Neo4j Browser: :play startup
# Or via cypher-shell:
cypher-shell -a bolt://localhost:7687 -u neo4j -p <password>
```

## Logs Location

- **Celery Worker**: `logs/celery_worker.log`
- **FastAPI**: stdout (or configure in production)
- **Redis**: Depends on installation
- **Neo4j**: `<neo4j-home>/logs/`

## Health Check Endpoints

After deployment, verify:

```bash
# FastAPI Health
curl http://localhost:8000/docs

# Celery Status
celery -A backend.celery_config inspect ping

# Redis Status
redis-cli ping
# Expected: PONG

# Neo4j Status
curl http://localhost:7474

# API Endpoints
curl http://localhost:8000/api/tasks
```

## Backup Strategy

### Before Production
- [ ] Back up .env file (secrets)
- [ ] Back up Neo4j database
- [ ] Test restore procedures

### Regular Maintenance
- [ ] Daily: .env backup
- [ ] Weekly: Neo4j full backup
- [ ] Monthly: Disaster recovery drill
- [ ] Quarterly: Security audit

## Scaling Considerations

### For High Load
1. **More Celery Workers**
   ```bash
   celery -A backend.celery_config worker -l info -c 8
   ```

2. **Redis Cluster**
   - Move Redis to separate server
   - Consider Redis Sentinel for HA

3. **Neo4j Cluster**
   - Neo4j Enterprise with clustering
   - Read replicas for reports

4. **Load Balancing**
   - Multiple FastAPI instances
   - Nginx or HAProxy in front

## Rollback Plan

If deployment fails:

1. Stop services
   ```bash
   # Ctrl+C in all terminals
   ```

2. Revert code changes
   ```bash
   git checkout <previous-version>
   ```

3. Restore database backup
   ```bash
   # Neo4j restore procedures
   ```

4. Verify all checks pass
   ```bash
   python validate_startup.py
   ```

5. Restart services

## Support Resources

- **Documentation**: See `CELERY_SETUP.md` and `QUICK_START.md`
- **API Docs**: http://localhost:8000/docs (Swagger)
- **Flower Monitoring**: http://localhost:5555
- **GitHub Webhooks**: https://docs.github.com/webhooks
- **Celery Documentation**: https://docs.celeryproject.io/

---

**Deployment Ready!** When all checks pass, system is ready for production use.
