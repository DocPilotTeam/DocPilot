@echo off
REM Flower Celery Monitoring UI Startup Script for Windows
REM Starts Flower web interface for monitoring Celery tasks

echo Starting Flower Celery Monitoring UI...

REM Activate virtual environment if it exists
if exist myenv\Scripts\activate.bat (
    call myenv\Scripts\activate.bat
)

REM Start Flower
REM Default port is 5555, can be changed with --port flag
flower -A backend.celery_config --port=5555 --broker=redis://localhost:6379/0 --url_prefix=flower

echo Flower stopped.
pause
