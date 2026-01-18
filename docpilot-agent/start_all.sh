#!/bin/bash
# Complete Application Startup Script
# Starts FastAPI server and Celery worker in separate processes

set -e

echo "=========================================="
echo "DocPilot Agent - Complete Startup"
echo "=========================================="

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "myenv" ]; then
    echo "Activating virtual environment..."
    source myenv/bin/activate
fi

# Check if Redis is running
echo "Checking Redis connection..."
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis CLI not found. Make sure Redis is running on localhost:6379"
else
    if redis-cli ping &> /dev/null; then
        echo "✓ Redis is running"
    else
        echo "⚠️  Redis is not responding. Please start Redis first."
        echo "  On macOS: brew services start redis"
        echo "  On Linux: sudo systemctl start redis-server"
        echo "  On Windows: redis-server.exe or WSL"
    fi
fi

# Start Celery worker in background
echo ""
echo "Starting Celery Worker..."
celery -A backend.celery_config worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000 \
    --logfile=logs/celery_worker.log \
    --pidfile=celery_worker.pid \
    &
WORKER_PID=$!
echo "Celery Worker PID: $WORKER_PID"

# Start FastAPI server
echo ""
echo "Starting FastAPI Server..."
uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info

# Cleanup on exit
echo ""
echo "Shutting down Celery Worker..."
kill $WORKER_PID 2>/dev/null || true

echo "=========================================="
echo "Application stopped"
echo "=========================================="
