from fastapi import APIRouter, HTTPException
from backend.agents.docgen.doc_generator import generate_docs

from backend.api.parser_api import RepoNameRequest
do_gen_router = APIRouter()

#DocGen Integration Endpoint
@do_gen_router.post("/generate-docs")
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