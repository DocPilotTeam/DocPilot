from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from backend.agents.parser.parser_manager import ParserManager
from backend.db.data import user_repo_db  # <-- in-memory DB storing cloned repo info
from backend.agents.docgen.doc_generator import generate_docs

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

    parsed_files = []

    try:
        # Parse all code files inside repository
        for root, dirs, files in os.walk(repo_path):
            for f in files:
                file_path = os.path.join(root, f)
                result = manager.parse(file_path)

                if not result:
                    continue

                parsed_files.append(result)

    finally:
        print(f"[Parsing Complete] Parsed {len(parsed_files)} files in {proj_name}")

    return {
        "status": "success",
        "total_files": len(parsed_files),
        "data": parsed_files
    }


#DocGen Integration Endpoint
@router.post("/generate-docs")
def generate_documentation(request: RepoNameRequest):
    projName=request.proj_name

    # if projName not in user_repo_db:
    #     raise HTTPException(status_code=404, detail="Project not found in UserRepos")
    
    try:
        documentation=generate_docs(projName)
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Failed to generate documenetation with error: {str(e)} ")
    
    return{
        "message": "Documentation generated successfully",
        "documentation": documentation,
        "project": projName,
        "status": "success"
    }