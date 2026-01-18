@echo off
REM =========================================
REM DocPilot - Start All Services
REM =========================================

echo.
echo ============================================
echo DocPilot Agent - Services Startup
echo ============================================
echo.

REM Check if Redis is installed
echo [1/4] Checking Redis...
where redis-server >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Redis is NOT installed!
    echo.
    echo Install Redis from:
    echo   - Windows (WSL): wsl redis-server
    echo   - Windows (Memurai): https://github.com/microsoftarchive/memurai-db
    echo   - Or use Windows Subsystem for Linux (WSL)
    echo.
    echo Quick setup with WSL:
    echo   wsl -l -v
    echo   wsl redis-server
    echo.
    pause
    exit /b 1
)

echo [1/4] ✓ Redis found. Starting...
start "Redis Server" redis-server
timeout /t 3 /nobreak

REM Check Redis is running
echo [2/4] Checking Redis connection...
redis-cli ping >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Cannot connect to Redis!
    pause
    exit /b 1
)
echo [2/4] ✓ Redis is running

REM Check Neo4j
echo [3/4] Checking Neo4j connection...
curl -s http://localhost:7474 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Neo4j might not be running at http://localhost:7474
    echo Make sure Neo4j is running before starting tasks
)
echo [3/4] ✓ Proceeding...

REM Start Celery Worker
echo [4/4] Starting Celery Worker...
start "Celery Worker" myenv\Scripts\celery -A backend.celery_config worker -l info
timeout /t 2 /nobreak

REM Start FastAPI
echo.
echo ✓ All services starting...
echo.
echo Services:
echo   - Redis Server: http://localhost:6379
echo   - Celery Worker: Running in separate window
echo   - FastAPI: Starting on http://localhost:8000
echo   - Neo4j: http://localhost:7474
echo.

cd backend
start "FastAPI Server" myenv\..\Scripts\uvicorn main:app --reload --port 8000

echo.
echo ============================================
echo Services started! Open http://localhost:8000
echo ============================================
echo.

pause
