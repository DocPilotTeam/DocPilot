from .supabase_client import supabase

def insert_repo(proj_name, repo_url, branch, auth_token):
    return supabase.table("repos").insert({
        "proj_name": proj_name,
        "repo_url": repo_url,
        "branch": branch,
        "auth_token": auth_token,       
    }).execute()


def get_repo_by_url(repo_url: str):
    return supabase.table("repos") \
        .select("*") \
        .eq("repo_url", repo_url) \
        .limit(1) \
        .execute()

