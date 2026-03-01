from .supabase_client import supabase
from datetime import datetime
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
def insert_repo(proj_name, repo_url, branch, auth_token):
    """
    Insert repository record into Supabase with automatic retry
    """
    logger.info(f"Inserting repo: {proj_name} from {repo_url}")
    return supabase.table("repos").insert({
        "proj_name": proj_name,
        "repo_url": repo_url,
        "branch": branch,
        "auth_token": auth_token,       
    }).execute()


@retry_on_network_error(max_retries=3, delay=1)
def get_repo_by_url(repo_url: str):
    """
    Retrieve repository by URL with automatic retry
    """
    logger.info(f"Fetching repo by URL: {repo_url}")
    return supabase.table("repos") \
        .select("*") \
        .eq("repo_url", repo_url) \
        .limit(1) \
        .execute()


@retry_on_network_error(max_retries=3, delay=1)
def save_documentation(proj_name, documentation_content, repo_url=None):
    """
    Save generated documentation to Supabase with automatic retry
    
    Args:
        proj_name: Project name
        documentation_content: The generated README markdown content
        repo_url: Optional repository URL
        
    Returns:
        Supabase insert response
    """
    logger.info(f"Saving documentation for project: {proj_name}")
    return supabase.table("documentation").insert({
        "proj_name": proj_name,
        "repo_url": repo_url,
        "content": documentation_content,
        "generated_at": datetime.utcnow().isoformat(),
        "status": "completed"
    }).execute()


@retry_on_network_error(max_retries=3, delay=1)
def get_documentation_by_project(proj_name):
    """
    Retrieve documentation for a specific project with automatic retry
    
    Args:
        proj_name: Project name to retrieve docs for
        
    Returns:
        Supabase query response with documentation record
    """
    logger.info(f"Fetching documentation for project: {proj_name}")
    return supabase.table("documentation") \
        .select("*") \
        .eq("proj_name", proj_name) \
        .order("generated_at", desc=True) \
        .limit(1) \
        .execute()


@retry_on_network_error(max_retries=3, delay=1)
def get_all_documentation():
    """
    Retrieve all documented projects with automatic retry
    
    Returns:
        Supabase query response with all documentation records
    """
    logger.info("Fetching all documentation")
    return supabase.table("documentation") \
        .select("proj_name, repo_url, generated_at, id") \
        .order("generated_at", desc=True) \
        .execute()


@retry_on_network_error(max_retries=3, delay=1)
def update_documentation(proj_name, documentation_content):
    """
    Update existing documentation for a project with automatic retry
    
    Args:
        proj_name: Project name
        documentation_content: Updated README markdown content
        
    Returns:
        Supabase update response
    """
    logger.info(f"Updating documentation for project: {proj_name}")
    return supabase.table("documentation") \
        .update({
            "content": documentation_content,
            "generated_at": datetime.utcnow().isoformat()
        }) \
        .eq("proj_name", proj_name) \
        .execute()


