@echo off
REM Celery Worker Startup Script for Windows
REM Starts Celery worker processes

echo Starting Celery Worker...

REM Activate virtual environment if it exists
if exist myenv\Scripts\activate.bat (
    call myenv\Scripts\activate.bat
)

REM Start Celery worker
REM Using 4 workers by default, can be changed with --concurrency flag
celery -A backend.celery_config worker --loglevel=info --concurrency=4 --pool=solo --hostname=worker1@%%h --max-tasks-per-child=1000 --time-limit=1800 --soft-time-limit=1500

echo Celery worker stopped.
pause
