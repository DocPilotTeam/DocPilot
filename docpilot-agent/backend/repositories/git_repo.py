import httpx

GITHUB_API = "https://api.github.com/repos"

async def validate_repo_access(owner: str, name: str, access_token: str):
    url = f"{GITHUB_API}/{owner}/{name}"
    async with httpx.AsyncClient() as client:
        res = await client.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if res.status_code != 200:
        return None

    return res.json()
