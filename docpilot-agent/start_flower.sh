#!/bin/bash
# Flower Celery Monitoring UI Startup Script
# Starts Flower web interface for monitoring Celery tasks

set -e

echo "Starting Flower Celery Monitoring UI..."

# Navigate to project root
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "myenv" ]; then
    source myenv/bin/activate
fi

# Start Flower
# Default port is 5555, can be changed with --port flag
flower -A backend.celery_config \
    --port=5555 \
    --broker=redis://localhost:6379/0 \
    --url_prefix=flower \
    --persistent=True \
    --db=/tmp/flower.db

echo "Flower stopped."
