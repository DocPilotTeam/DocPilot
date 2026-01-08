from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from backend.core.config import settings
from backend.auth.github import exchange_code_for_token, get_github_user
from backend.users.user_queries import upsert_user, get_user_by_github_id
from backend.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


# 🔹 STEP 1: Redirect user to GitHub OAuth
@router.get("/login/github")
def github_login():
    github_oauth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        "&scope=repo read:user"
    )
    return RedirectResponse(github_oauth_url)


# 🔹 STEP 2: GitHub redirects here with ?code=
@router.get("/github/callback")
async def github_callback(code: str):
    try:
        # Exchange code for GitHub access token
        access_token = await exchange_code_for_token(code)

        # Fetch GitHub user
        gh_user = await get_github_user(access_token)

        # Store / update user in DB
        upsert_user(gh_user)

        user = get_user_by_github_id(gh_user["id"]).data

        # Create internal JWT
        jwt_token = create_access_token({
            "user_id": user["id"],
            "github_id": user["github_id"],
            "github_token": access_token
        })

        return {
            "access_token": jwt_token,
            "user": {
                "id": user["id"],
                "username": user["username"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
