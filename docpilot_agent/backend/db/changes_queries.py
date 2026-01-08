from .supabase_client import supabase

def save_changed_files(repo_id, commit_hash, changed_files):
    data = [
        {
            "repo_id": repo_id,
            "commit_hash": commit_hash,
            "file_path": f,
            "change_type": "modified"
        }
        for f in changed_files
    ]

    return supabase.table("changed_files").insert(data).execute()
