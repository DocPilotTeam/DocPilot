from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from backend.core.config import settings
from backend.auth.github import exchange_code_for_token, get_github_user, get_user_repositories
from backend.users.user_queries import upsert_user, get_user_by_github_id
from backend.auth.jwt import create_access_token
from celery.utils.log import get_task_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_task_logger(__name__)


# 🔹 STEP 1: Redirect user to GitHub OAuth
@router.get("/login/github")
def github_login():
    """
    Redirect user to GitHub OAuth authorization page
    """
    try:
        if not settings.GITHUB_CLIENT_ID:
            raise HTTPException(
                status_code=500,
                detail="GitHub Client ID not configured"
            )
        
        github_oauth_url = (
            "https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
            "&scope=repo read:user"
        )
        logger.info(f"Redirecting to GitHub OAuth: {github_oauth_url[:50]}...")
        return RedirectResponse(github_oauth_url)
    
    except Exception as e:
        logger.error(f"Error during GitHub login redirect: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 STEP 2: GitHub redirects here with ?code=
@router.get("/github/callback")
async def github_callback(code: str):
    """
    GitHub OAuth callback endpoint
    Exchanges authorization code for access token and creates user session
    """
    try:
        if not code:
            logger.warning("GitHub callback received without authorization code")
            raise HTTPException(status_code=400, detail="Authorization code missing")
        
        logger.info(f"GitHub callback received with code: {code[:10]}...")
        
        # Step 1: Exchange code for GitHub access token
        try:
            logger.info("Attempting to exchange authorization code for access token")
            access_token = await exchange_code_for_token(code)
            logger.info("Successfully obtained access token from GitHub")
        except Exception as token_error:
            logger.error(f"Failed to exchange code for token: {str(token_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to authenticate with GitHub: {str(token_error)}"
            )

        # Step 2: Fetch GitHub user profile
        try:
            logger.info("Fetching GitHub user profile")
            gh_user = await get_github_user(access_token)
            logger.info(f"GitHub user fetched: {gh_user.get('login', 'unknown')}")
        except Exception as user_error:
            logger.error(f"Failed to fetch GitHub user: {str(user_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch GitHub user profile: {str(user_error)}"
            )

        # Step 3: Fetch user's repositories
        try:
            logger.info("Fetching GitHub user repositories")
            repositories = await get_user_repositories(access_token)
            logger.info(f"Fetched {len(repositories)} repositories")
        except Exception as repo_error:
            logger.warning(f"Failed to fetch repositories (non-critical): {str(repo_error)}")
            repositories = []  # Continue without repositories

        # Step 4: Store/update user in database
        try:
            logger.info(f"Storing/updating user in database: {gh_user.get('id')}")
            upsert_user(gh_user)
            
            user_query_result = get_user_by_github_id(gh_user["id"])
            if not user_query_result.data:
                raise Exception("User not found in database after insertion")
            
            user = user_query_result.data[0] if isinstance(user_query_result.data, list) else user_query_result.data
            logger.info(f"User stored/updated successfully: {user.get('id')}")
        except Exception as db_error:
            logger.error(f"Failed to store user in database: {str(db_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create user session: {str(db_error)}"
            )

        # Step 5: Create internal JWT token
        try:
            logger.info("Creating JWT access token")
            jwt_token = create_access_token({
                "user_id": user.get("id"),
                "github_id": user.get("github_id"),
                "github_token": access_token
            })
            logger.info("JWT token created successfully")
        except Exception as jwt_error:
            logger.error(f"Failed to create JWT token: {str(jwt_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session token: {str(jwt_error)}"
            )

        logger.info(f"GitHub OAuth flow completed for user: {gh_user.get('login')}")
        
        return {
            "access_token": jwt_token,
            "user": {
                "id": user.get("id"),
                "username": user.get("username"),
                "github_id": user.get("github_id")
            },
            "repositories": repositories,
            "status": "success"
        }

    except HTTPException:
        raise  # Re-raise HTTPExceptions
    except Exception as e:
        logger.error(f"Unexpected error in GitHub callback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"GitHub authentication failed: {str(e)}"
        )
