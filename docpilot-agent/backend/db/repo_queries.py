from .supabase_client import supabase

def insert_repo(proj_name, repo_url, branch, auth_token):
    return supabase.table("repos").insert({
        "proj_name": proj_name,
        "repo_url": repo_url,
        "branch": branch,
        "auth_token": auth_token,       
    }).execute()


def get_repo_by_name(proj_name: str):
    return supabase.table("repos") \
        .select("*") \
        .eq("proj_name", proj_name) \
        .limit(1) \
        .execute()

