"""
Celery Configuration Module
Configures Celery task queue with Redis as message broker
Supports both local and hosted Redis services
"""
import os
from celery import Celery
from dotenv import load_dotenv
import ssl

load_dotenv()

# Create Celery app
app = Celery(
    'docpilot_agent',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
)

# Configure Celery settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Broker connection settings (important for hosted Redis)
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_channel_error_retry=5.0,
    broker_pool_limit=None,  # Use unlimited connections for hosted Redis
    broker_heartbeat=30,  # Send heartbeat every 30 seconds to keep connection alive
    broker_socket_keepalive=True,  # Enable TCP keepalive
    broker_socket_keepalive_options={
        1: 30,  # TCP_KEEPIDLE - start after 30s
        2: 5,   # TCP_KEEPINTVL - interval 5s
        3: 5,   # TCP_KEEPCNT - 5 probes
    },
    
    # Connection pool settings for hosted Redis stability
    broker_connection_retry_on_error=True,
    broker_login_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    
    # Kombu transport settings
    broker_transport_options={
        'priority_steps': list(range(10)),
        'sep': '.',
        'queue_order_strategy': 'priority',
        'master_name': 'mymaster',
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            1: 30,  # TCP_KEEPIDLE
            2: 5,   # TCP_KEEPINTVL  
            3: 5,   # TCP_KEEPCNT
        },
    },
)

# Auto-discover tasks from backend modules
app.autodiscover_tasks(['backend.jobs'])
