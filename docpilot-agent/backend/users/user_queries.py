from backend.db.supabase_client import supabase

def upsert_user(gh_user: dict):
    return supabase.table("users").upsert({
        "github_id": gh_user["id"],
        "username": gh_user["login"],
        "email": gh_user.get("email"),
        "avatar_url": gh_user.get("avatar_url"),
    }).execute()

def get_user_by_github_id(github_id: int):
    return supabase.table("users") \
        .select("*") \
        .eq("github_id", github_id) \
        .single() \
        .execute()
