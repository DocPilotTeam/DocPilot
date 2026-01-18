#!/bin/bash
# Celery Beat Scheduler Startup Script
# Starts Celery beat scheduler for periodic tasks

set -e

echo "Starting Celery Beat Scheduler..."

# Navigate to project root
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "myenv" ]; then
    source myenv/bin/activate
fi

# Start Celery beat scheduler
celery -A backend.celery_config beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

echo "Celery beat stopped."
