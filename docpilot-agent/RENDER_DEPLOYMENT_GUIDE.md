# Quick Fix Guide - Production Essentials for Render

Complete these fixes before deploying to Render. Estimated time: 2-3 hours.

---

## 1. Add Health Check Endpoints (15 min)

**File**: `backend/api/health.py` (Create new)

```python
from fastapi import APIRouter, HTTPException
from backend.db.neo4j_connect import driver
import logging

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

@router.get("/health", tags=["Health"])
async def health():
    """Basic health check"""
    return {"status": "ok", "service": "docpilot-api"}

@router.get("/health/live", tags=["Health"])  
async def liveness():
    """Liveness probe for Render"""
    return {"status": "alive"}

@router.get("/health/ready", tags=["Health"])
async def readiness():
    """Readiness probe - check critical dependencies"""
    try:
        driver.verify_connectivity()
        return {"status": "ready", "neo4j": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")
```

**Update** `backend/main.py`:
```python
from backend.api.health import router as health_router

# Add before other routers:
app.include_router(health_router, prefix="/api")
```

---

## 2. Add CORS Middleware (10 min)

**Update** `backend/main.py` (Add at top after imports):

```python
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Add CORS middleware
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Add to .env.production**:
```
CORS_ORIGINS=https://yourdomain.onrender.com,http://localhost:3000
```

---

## 3. Add Environment Variable Validation (10 min)

**File**: `backend/startup.py` (Create new)

```python
import os
import sys
import logging

logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables on startup"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    required_vars = {
        "NEO4J_URL": "Neo4j database URL",
        "NEO4J_PASS": "Neo4j password",
        "OPENAI_API_KEY": "OpenRouter API key",
        "CELERY_BROKER_URL": "Redis broker URL",
    }
    
    # JWT_SECRET required only in production
    if environment == "production":
        required_vars["JWT_SECRET"] = "JWT signing secret"
        required_vars["GITHUB_CLIENT_ID"] = "GitHub OAuth client ID"
        required_vars["GITHUB_CLIENT_SECRET"] = "GitHub OAuth secret"
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")
    
    if missing:
        error_msg = f"Missing required environment variables:\n" + "\n".join(f"  - {m}" for m in missing)
        logger.error(error_msg)
        if environment == "production":
            sys.exit(1)
        else:
            logger.warning(f"Development mode: proceeding without all variables")
    
    logger.info("Environment validation passed")

async def startup_event():
    """Startup event handler"""
    validate_environment()
    logger.info("Application startup complete")
    
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Application shutting down gracefully")
```

**Update** `backend/main.py`:
```python
from backend.startup import startup_event, shutdown_event

@app.on_event("startup")
async def startup():
    await startup_event()

@app.on_event("shutdown")  
async def shutdown():
    await shutdown_event()
```

---

## 4. Add Structured Logging (15 min)

**File**: `backend/logging_config.py` (Create new)

```python
import logging
import json
from logging import Formatter
import sys

class JsonFormatter(Formatter):
    """Structured JSON logging for better log aggregation"""
    
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'task_id'):
            log_data['task_id'] = record.task_id
        if hasattr(record, 'project'):
            log_data['project'] = record.project
            
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def configure_logging():
    """Configure application logging"""
    import os
    
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
```

**Update** `backend/main.py` (At very top):
```python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging before anything else
from backend.logging_config import configure_logging
configure_logging()

# Then import other modules
from fastapi import FastAPI
# ... rest of imports
```

---

## 5. Add Global Exception Handler (10 min)

**Update** `backend/main.py` (After creating app, before routers):

```python
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}",
        exc_info=exc,
        extra={"request_id": request_id}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

---

## 6. Create Render Configuration Files (10 min)

**File**: `render.yaml` (In project root)

```yaml
services:
  - type: web
    name: docpilot-api
    env: python
    plan: standard
    pythonVersion: 3.11
    
    buildCommand: |
      cd docpilot-agent && \
      pip install -r requirements.txt
    
    startCommand: |
      cd docpilot-agent && \
      python -m uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port $PORT \
        --workers 1
    
    healthCheckPath: /api/health
    healthCheckStartupFailureThresholdCount: 10
    
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: PYTHONUNBUFFERED
        value: "1"
```

---

## 7. Create .env.example (5 min)

**File**: `.env.example` (In project root)

```bash
# Environment
ENVIRONMENT=development

# Neo4j
NEO4J_URL=neo4j+ssc://your-instance.databases.neo4j.io
NEO4J_PASS=your-password

# OpenAI/OpenRouter
OPENAI_API_KEY=sk-xxxx

# GitHub OAuth (for repo integration)
GITHUB_CLIENT_ID=your-app-id
GITHUB_CLIENT_SECRET=your-secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback

# JWT
JWT_SECRET=your-secret-key-change-in-production

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
```

---

## 8. Test Locally Before Deploying

```bash
# Install dependencies
pip install -r requirements.txt

# Set test environment
SET ENVIRONMENT=development
SET NEO4J_URL=your-test-instance
SET NEO4J_PASS=your-test-password
SET OPENAI_API_KEY=your-test-key
SET CELERY_BROKER_URL=redis://localhost:6379/0

# Run API
python -m uvicorn backend.main:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/health/ready

# Test with GitHub token
curl -X POST http://localhost:8000/api/repositories/process \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "test",
    "repo_url": "https://github.com/user/repo",
    "branch": "main",
    "github_token": "ghp_xxx"
  }'
```

---

## 9. Deployment Checklist

Before clicking "Deploy" on Render:

- [ ] All code changes committed and pushed to Git
- [ ] All environment variables set in Render dashboard
- [ ] `.env.example` created showing required variables
- [ ] Health check endpoints tested locally
- [ ] CORS origins configured for your frontend
- [ ] JWT_SECRET is a strong random value
- [ ] Neo4j connection verified
- [ ] Redis connection verified
- [ ] OpenRouter API key validated

---

## Render Environment Variables to Set

In Render Dashboard → Environment:

```
ENVIRONMENT=production
NEO4J_URL=<your-aura-url>
NEO4J_PASS=<your-password>
OPENAI_API_KEY=<your-openrouter-key>
GITHUB_CLIENT_ID=<your-oauth-id>
GITHUB_CLIENT_SECRET=<your-oauth-secret>
GITHUB_REDIRECT_URI=https://your-render-url.onrender.com/api/auth/github/callback
JWT_SECRET=<strong-random-secret>
CELERY_BROKER_URL=<your-redis-url>
CELERY_RESULT_BACKEND=<your-redis-url>
CORS_ORIGINS=https://your-frontend.onrender.com,https://your-domain.com
```

---

## Estimated Deployment Timeline

- Code changes: 2-3 hours
- Testing locally: 30 min
- Deploy to Render: 10 min
- Monitor initial run: 15 min

**Total: ~3-4 hours**

---

## Support

| Issue | Solution |
|-------|----------|
| Health check fails | Check Neo4j connectivity in Render logs |
| Cannot connect to Redis | Verify CELERY_BROKER_URL in environment |
| CORS errors | Check CORS_ORIGINS environment variable |
| JWT errors | Ensure JWT_SECRET is set |
| LLM 404 errors | Verify OPENAI_API_KEY on OpenRouter account |
