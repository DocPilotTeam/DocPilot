from backend.db.supabase_client import supabase
from celery.utils.log import get_task_logger
from functools import wraps
import time

logger = get_task_logger(__name__)


def retry_on_network_error(max_retries=3, delay=1):
    """
    Decorator to retry database operations on network/DNS errors
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_retries + 1):
                try:
                    logger.debug(f"Attempting {func.__name__} (attempt {attempt}/{max_retries})")
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()
                    
                    # Only retry on network/DNS errors
                    if any(x in error_msg for x in ['getaddrinfo', 'connection', 'timeout', 'dns']):
                        logger.warning(
                            f"Network error in {func.__name__} (attempt {attempt}/{max_retries}): {str(e)}"
                        )
                        if attempt < max_retries:
                            wait_time = delay * attempt  # Exponential backoff
                            logger.info(f"Retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"All {max_retries} retry attempts failed for {func.__name__}")
                    else:
                        # Not a network error, fail immediately
                        logger.error(f"Non-network error in {func.__name__}: {str(e)}")
                        raise
            
            # If we get here, all retries failed
            raise Exception(f"Failed after {max_retries} attempts: {str(last_error)}")
        
        return wrapper
    return decorator


@retry_on_network_error(max_retries=3, delay=1)
def upsert_user(gh_user: dict):
    """
    Insert or update user in Supabase
    With automatic retry on network errors (up to 3 attempts)
    """
    try:
        logger.info(f"Upserting user: {gh_user.get('login')} (github_id: {gh_user['id']})")
        
        result = supabase.table("users").upsert(
            {
                "github_id": gh_user["id"],
                "username": gh_user["login"],
                "email": gh_user.get("email"),
                "avatar_url": gh_user.get("avatar_url"),
            },
            on_conflict="github_id"
        ).execute()
        
        logger.info(f"User upserted successfully: {gh_user.get('login')}")
        return result
    
    except Exception as e:
        logger.error(f"Error upserting user {gh_user.get('login')}: {str(e)}")
        raise


@retry_on_network_error(max_retries=3, delay=1)
def get_user_by_github_id(github_id: int):
    """
    Fetch user from Supabase by GitHub ID
    With automatic retry on network errors (up to 3 attempts)
    """
    try:
        logger.info(f"Fetching user with github_id: {github_id}")
        
        result = supabase.table("users") \
            .select("*") \
            .eq("github_id", github_id) \
            .single() \
            .execute()
        
        logger.info(f"User fetched successfully: {github_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error fetching user {github_id}: {str(e)}")
        raise

