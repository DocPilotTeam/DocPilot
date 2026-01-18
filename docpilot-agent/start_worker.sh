#!/bin/bash
# Celery Worker Startup Script
# Starts Celery worker processes

set -e

echo "Starting Celery Worker..."

# Navigate to project root
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "myenv" ]; then
    source myenv/bin/activate
fi

# Start Celery worker with specified concurrency
# Using 4 workers by default, can be changed with --concurrency flag
celery -A backend.celery_config worker \
    --loglevel=info \
    --concurrency=4 \
    --pool=prefork \
    --hostname=worker1@%h \
    --max-tasks-per-child=1000 \
    --time-limit=1800 \
    --soft-time-limit=1500

echo "Celery worker stopped."
