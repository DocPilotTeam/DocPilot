from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from agents.parser.parser_manager import ParserManager
from db.data import user_repo_db  # <-- in-memory DB storing cloned repo info

router = APIRouter()
manager = ParserManager()

# ------------------------------
# Request Models
# ------------------------------
class RepoNameRequest(BaseModel):
    proj_name: str  # Project name stored in UserRepos


# ------------------------------
# Parse Repository by Project Name
# ------------------------------
@router.post("/parse-repo")
@router.post("/parse-repo")
def parse_repo(request: RepoNameRequest):
    proj_name = request.proj_name

    # Check if project exists in our DB
    if proj_name not in user_repo_db:
        raise HTTPException(status_code=404, detail="Project not found in UserRepos")

    repo_path = user_repo_db[proj_name]["local_path"]

    if not os.path.isdir(repo_path):
        raise HTTPException(status_code=404, detail="Repository directory not found")

    # Allowed real code file extensions → all others will be skipped
    allowed_ext = {".py", ".java", ".js", ".ts"}

    parsed_files = []
    for root, dirs, files in os.walk(repo_path):
        for f in files:
            file_path = os.path.join(root, f)

            ext = os.path.splitext(f)[1].lower()

            # Skip all unwanted files (md, txt, gitignore, json, xml, png, etc)
            if ext not in allowed_ext:
                continue

            result = manager.parse(file_path)

            # Skip if parser returns None (unknown / unsupported language)
            if not result:
                continue

            parsed_files.append(result)

    return {
        "status": "success",
        "total_files": len(parsed_files),
        "data": parsed_files
    }
