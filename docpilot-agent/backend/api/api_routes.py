from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import shutil

from agents.parser.parser_manager import ParserManager
from db.data import user_repo_db  # <-- in-memory DB storing cloned repo info

router = APIRouter()
manager = ParserManager()

# Request Models
class RepoNameRequest(BaseModel):
    proj_name: str  # Project name stored in UserRepos


# Parse Repository by Project Name
@router.post("/parse-repo")
def parse_repo(request: RepoNameRequest):
    proj_name = request.proj_name

    # Check if project exists in our DB
    if proj_name not in user_repo_db:
        raise HTTPException(status_code=404, detail="Project not found in UserRepos")

    repo_path = user_repo_db[proj_name]["local_path"]

    if not os.path.isdir(repo_path):
        raise HTTPException(status_code=404, detail="Repository directory not found")

    # Allowed real code file extensions
    allowed_ext = {".py", ".java", ".js", ".ts"}

    parsed_files = []

    try:
        # Parse all code files inside repository
        for root, dirs, files in os.walk(repo_path):
            for f in files:
                file_path = os.path.join(root, f)

                ext = os.path.splitext(f)[1].lower()

                # Skip non-code files
                if ext not in allowed_ext:
                    continue

                result = manager.parse(file_path)

                if not result:
                    continue

                parsed_files.append(result)

    finally:
        try:
            print("Trying to delete:", repo_path)

            import stat
            def remove_readonly(func, path, excinfo):
                os.chmod(path, stat.S_IWRITE)
                func(path)

            shutil.rmtree(repo_path, onerror=remove_readonly)
            print(f"[Cleanup] Deleted local repo → {repo_path}")

        except Exception as e:
            print(f"[Cleanup Error] Could not delete repo: {e}")

    # Remove from in-memory DB
    if proj_name in user_repo_db:
        del user_repo_db[proj_name]
        print(f"[Cleanup] Removed {proj_name} from in-memory DB")


    return {
        "status": "success",
        "total_files": len(parsed_files),
        "data": parsed_files
    }
