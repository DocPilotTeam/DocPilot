from backend.db.supabase_client import supabase

def get_repo_by_user(user_id: str, owner: str, name: str):
    return supabase.table("repos") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("owner", owner) \
        .eq("name", name) \
        .execute()

def insert_repo(user_id: str, owner: str, name: str, private: bool):
    return supabase.table("repos").insert({
        "user_id": user_id,
        "owner": owner,
        "name": name,
        "private": private,
        "status": "IMPORTED"
    }).execute()

def get_repo_by_id(repo_id: str, user_id: str):
    return supabase.table("repos") \
        .select("*") \
        .eq("id", repo_id) \
        .eq("user_id", user_id) \
        .single() \
        .execute()
