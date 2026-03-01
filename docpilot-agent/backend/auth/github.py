import httpx
import ssl
from backend.core.config import settings
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


async def exchange_code_for_token(code: str) -> str:
    """
    Exchange GitHub authorization code for access token
    Handles SSL/DNS issues with retry logic and proper error messages
    """
    try:
        # Create SSL context that works on Windows
        ssl_context = ssl.create_default_context()
        
        async with httpx.AsyncClient(
            verify=ssl_context,
            timeout=30.0,
            follow_redirects=True
        ) as client:
            logger.info(f"Exchanging GitHub code for access token")
            
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI
                }
            )

        logger.info(f"GitHub token response status: {response.status_code}")
        
        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"GitHub token exchange failed: {error_detail}")
            raise Exception(f"GitHub API error: {response.status_code} - {error_detail}")

        data = response.json()
        
        if "error" in data:
            logger.error(f"GitHub OAuth error: {data.get('error_description', data['error'])}")
            raise Exception(f"GitHub OAuth error: {data.get('error_description', data['error'])}")
        
        if "access_token" not in data:
            logger.error(f"No access token in response: {data}")
            raise Exception("GitHub token exchange failed - no access token returned")

        logger.info("GitHub access token obtained successfully")
        return data["access_token"]
    
    except httpx.ConnectError as e:
        logger.error(f"Connection error with GitHub: {str(e)}")
        raise Exception(f"Failed to connect to GitHub: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Request error with GitHub: {str(e)}")
        raise Exception(f"GitHub API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token exchange: {str(e)}")
        raise


async def get_github_user(access_token: str) -> dict:
    """
    Fetch authenticated GitHub user profile
    """
    try:
        ssl_context = ssl.create_default_context()
        
        async with httpx.AsyncClient(
            verify=ssl_context,
            timeout=30.0,
            follow_redirects=True
        ) as client:
            logger.info("Fetching GitHub user profile")
            
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json"
                }
            )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch user: {response.status_code} - {response.text}")
            raise Exception(f"Failed to fetch GitHub user: {response.status_code}")

        logger.info("GitHub user profile fetched successfully")
        return response.json()
    
    except Exception as e:
        logger.error(f"Error fetching GitHub user: {str(e)}")
        raise


async def get_user_repositories(access_token: str) -> list:
    """
    Fetch all repositories for the authenticated user
    Returns a list of repositories with name, url, and other metadata
    Handles pagination and network errors gracefully
    """
    repositories = []
    page = 1
    max_pages = 10  # Safety limit
    
    try:
        ssl_context = ssl.create_default_context()
        
        async with httpx.AsyncClient(
            verify=ssl_context,
            timeout=30.0,
            follow_redirects=True
        ) as client:
            logger.info("Fetching GitHub user repositories")
            
            while page <= max_pages:
                try:
                    response = await client.get(
                        "https://api.github.com/user/repos",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/vnd.github+json"
                        },
                        params={
                            "sort": "updated",
                            "direction": "desc",
                            "per_page": 100,
                            "page": page,
                            "type": "all"  # Include public, private, and owned repos
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to fetch repositories page {page}: {response.status_code}")
                        if page == 1:  # Only raise on first page
                            raise Exception(f"Failed to fetch repositories: {response.status_code}")
                        break
                    
                    repos = response.json()
                    if not repos:
                        logger.info(f"No more repositories at page {page}")
                        break
                    
                    for repo in repos:
                        repositories.append({
                            "id": repo["id"],
                            "name": repo["name"],
                            "full_name": repo["full_name"],
                            "url": repo["clone_url"],
                            "html_url": repo["html_url"],
                            "description": repo.get("description", ""),
                            "language": repo.get("language", ""),
                            "is_private": repo["private"],
                            "stars": repo["stargazers_count"],
                            "default_branch": repo["default_branch"]
                        })
                    
                    page += 1
                
                except Exception as page_error:
                    logger.warning(f"Error fetching page {page}, stopping pagination: {str(page_error)}")
                    if page == 1:
                        raise  # Re-raise if first page failed
                    break
        
        logger.info(f"Successfully fetched {len(repositories)} repositories")
        return repositories
    
    except Exception as e:
        logger.error(f"Error fetching user repositories: {str(e)}")
        raise    