import httpx
from backend.core.config import settings


async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
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

    data = response.json()
    if "access_token" not in data:
        raise Exception("GitHub token exchange failed")

    return data["access_token"]


async def get_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    return response.json()

async def get_user_repositories(access_token: str) -> list:
    """
    Fetch all repositories for the authenticated user
    Returns a list of repositories with name, url, and other metadata
    """
    repositories = []
    page = 1
    
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                "https://api.github.com/user/repos",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": 100,
                    "page": page,
                    "type": "all"  # Include public, private, and owned repos
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch repositories: {response.status_code}")
            
            repos = response.json()
            if not repos:
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
    
    return repositories    