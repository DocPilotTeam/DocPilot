from .supabase_client import supabase
from datetime import datetime

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


def save_documentation(proj_name, documentation_content, repo_url=None):
    """
    Save generated documentation to Supabase
    
    Args:
        proj_name: Project name
        documentation_content: The generated README markdown content
        repo_url: Optional repository URL
        
    Returns:
        Supabase insert response
    """
    return supabase.table("documentation").insert({
        "proj_name": proj_name,
        "repo_url": repo_url,
        "content": documentation_content,
        "generated_at": datetime.utcnow().isoformat(),
        "status": "completed"
    }).execute()


def get_documentation_by_project(proj_name):
    """
    Retrieve documentation for a specific project
    
    Args:
        proj_name: Project name to retrieve docs for
        
    Returns:
        Supabase query response with documentation record
    """
    return supabase.table("documentation") \
        .select("*") \
        .eq("proj_name", proj_name) \
        .order("generated_at", desc=True) \
        .limit(1) \
        .execute()


def get_all_documentation():
    """
    Retrieve all documented projects
    
    Returns:
        Supabase query response with all documentation records
    """
    return supabase.table("documentation") \
        .select("proj_name, repo_url, generated_at, id") \
        .order("generated_at", desc=True) \
        .execute()


def update_documentation(proj_name, documentation_content):
    """
    Update existing documentation for a project
    
    Args:
        proj_name: Project name
        documentation_content: Updated README markdown content
        
    Returns:
        Supabase update response
    """
    return supabase.table("documentation") \
        .update({
            "content": documentation_content,
            "generated_at": datetime.utcnow().isoformat()
        }) \
        .eq("proj_name", proj_name) \
        .execute()

