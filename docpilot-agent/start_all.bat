@echo off
REM Complete Application Startup Script for Windows
REM Starts FastAPI server and Celery worker in separate terminals

echo.
echo ==========================================
echo DocPilot Agent - Complete Startup
echo ==========================================
echo.

REM Activate virtual environment if it exists
if exist myenv\Scripts\activate.bat (
    echo Activating virtual environment...
    call myenv\Scripts\activate.bat
)

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Check for Redis
echo Checking Redis connection...
where redis-cli >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Redis CLI not found. Make sure Redis is running on localhost:6379
) else (
    redis-cli ping >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo OK - Redis is running
    ) else (
        echo WARNING: Redis is not responding. Please start Redis first.
    )
)

echo.
echo Starting Celery Worker in new terminal...
start "Celery Worker" cmd /k "celery -A backend.celery_config worker --loglevel=info --concurrency=4 --pool=solo --logfile=logs\celery_worker.log"

timeout /t 2 /nobreak

echo.
echo Starting FastAPI Server on http://localhost:8000
start "FastAPI Server" cmd /k "uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo ==========================================
echo Services started in separate terminals
echo FastAPI: http://localhost:8000
echo Flower (monitoring): http://localhost:5555
echo ==========================================
echo.
pause
