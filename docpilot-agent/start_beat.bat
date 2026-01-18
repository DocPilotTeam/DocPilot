@echo off
REM Celery Beat Scheduler Startup Script for Windows
REM Starts Celery beat scheduler for periodic tasks

echo Starting Celery Beat Scheduler...

REM Activate virtual environment if it exists
if exist myenv\Scripts\activate.bat (
    call myenv\Scripts\activate.bat
)

REM Start Celery beat scheduler
celery -A backend.celery_config beat --loglevel=info

echo Celery beat stopped.
pause
