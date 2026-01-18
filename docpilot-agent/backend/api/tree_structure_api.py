from fastapi import APIRouter, HTTPException
from backend.agents.diagramgen.tree_structure_agent import generate_directory_tree
from pathlib import Path

router = APIRouter(prefix="/structure", tags=["Structure"])

# Path to the UserRepos directory (two levels up from this file -> docpilot_agent/UserRepos)
USER_REPOS_DIR = Path(__file__).parents[2] / "UserRepos"


@router.get("/repo/{repo_name}")
def generate_repo_structure(repo_name: str):
    """
    Repo MUST already exist in UserRepos
    """
    repo_path = USER_REPOS_DIR / repo_name
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found in UserRepos")

    tree = generate_directory_tree(str(repo_path), root_name=repo_name)
    # Return as an array of lines so clients can render line breaks themselves
    structure_lines = tree.splitlines()

    return {
        "repo": repo_name,
        "structure": structure_lines
    }
