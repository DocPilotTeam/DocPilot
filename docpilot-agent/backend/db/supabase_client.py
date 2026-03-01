from supabase import create_client
import os
from dotenv import load_dotenv
import time
from celery.utils.log import get_task_logger

load_dotenv()

logger = get_task_logger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.error("Supabase environment variables are missing!")
    logger.error(f"SUPABASE_URL: {SUPABASE_URL}")
    logger.error(f"SUPABASE_SERVICE_KEY: {bool(SUPABASE_SERVICE_KEY)}")
    raise RuntimeError(
        "Missing Supabase configuration. "
        "Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file"
    )

logger.info(f"Initializing Supabase client with URL: {SUPABASE_URL[:50]}...")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    logger.error(f"This error often indicates DNS issues or network connectivity problems")
    raise RuntimeError(f"Supabase initialization failed: {str(e)}")

