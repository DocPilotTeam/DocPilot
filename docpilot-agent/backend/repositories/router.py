from fastapi import APIRouter, Depends, HTTPException
from backend.core.auth_dependency import get_current_user
from backend.users.user_queries import get_user_by_github_id
from backend.repositories.repo_queries import (
    get_repo_by_user,
    insert_repo
)
from backend.repositories.git_repo import validate_repo_access
from backend.db.supabase_client import supabase

router = APIRouter(prefix="/repos", tags=["repos"])

@router.post("/import")
async def import_repo(
    repo_url: str,
    user_id=Depends(get_current_user)
):
    try:
        # Parse URL
        parts = repo_url.rstrip("/").split("/")
        owner, name = parts[-2], parts[-1]

        # Get user GitHub token
        user = supabase.table("users") \
            .select("github_id, access_token") \
            .eq("id", user_id) \
            .single() \
            .execute().data

        # Validate access with GitHub
        repo_data = await validate_repo_access(
            owner,
            name,
            user["access_token"]
        )

        if not repo_data:
            raise HTTPException(status_code=403, detail="Repo access denied")

        # Check if already imported
        existing = get_repo_by_user(user_id, owner, name).data
        if existing:
            return existing[0]

        # Insert repo
        result = insert_repo(
            user_id,
            owner,
            name,
            repo_data["private"]
        )

        return result.data[0]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
