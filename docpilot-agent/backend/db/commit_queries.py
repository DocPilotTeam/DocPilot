from .supabase_client import supabase

def insert_commit(repo_id, commit_hash):
    return supabase.table("repo_commits").insert({
        "repo_id": repo_id,
        "last_commit": commit_hash
    }).execute()

def update_commit(repo_id, commit_hash):
    return supabase.table("repo_commits").update({
        "last_commit": commit_hash
    }).eq("repo_id", repo_id).execute()

def get_last_commit(repo_id):
    return supabase.table("repo_commits").select("*")\
        .eq("repo_id", repo_id).single().execute()
