from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from typing import Optional

from backend.agents.parser.parser_manager import ParserManager
from backend.db.data import user_repo_db  # <-- in-memory DB storing cloned repo info
from backend.agents.docgen.doc_generator import generate_docs
from backend.jobs.worker import (
    clone_repository,
    parse_repository,
    generate_cypher,
    build_knowledge_graph,
    generate_documentation_task,
    process_repository_pipeline
)
from backend.db.repo_queries import (
    get_documentation_by_project,
    get_all_documentation
)


router = APIRouter()
do_gen_router = APIRouter()
manager = ParserManager()

# Request Models
class RepoNameRequest(BaseModel):
    proj_name: str  # Project name stored in UserRepos


class ProcessRepoRequest(BaseModel):
    proj_name: str
    repo_url: str
    branch: str
    github_token: str


class TaskStatusRequest(BaseModel):
    task_id: str


# ===== LEGACY SYNCHRONOUS ENDPOINTS (kept for backward compatibility) =====

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


# DocGen Integration Endpoint
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


# ===== NEW ASYNC CELERY ENDPOINTS =====

@router.post("/process-repository")
def process_repository_async(request: ProcessRepoRequest):
    """
    Async endpoint to process a repository through the complete pipeline
    Returns task ID for status tracking
    """
    try:
        task = process_repository_pipeline.delay(
            request.proj_name,
            request.repo_url,
            request.branch,
            request.github_token
        )
        
        return {
            "status": "processing",
            "task_id": task.id,
            "project": request.proj_name,
            "message": "Repository processing started"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.post("/clone-repo-async")
def clone_repository_async(request: ProcessRepoRequest):
    """
    Async endpoint to clone/update repository
    Returns task ID for status tracking
    """
    try:
        task = clone_repository.delay(
            request.proj_name,
            request.repo_url,
            request.branch,
            request.github_token
        )
        
        return {
            "status": "processing",
            "task_id": task.id,
            "project": request.proj_name,
            "message": "Repository clone started"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start clone: {str(e)}")


@router.post("/parse-repo-async")
def parse_repository_async(request: RepoNameRequest):
    """
    Async endpoint to parse repository
    Returns task ID for status tracking
    """
    try:
        task = parse_repository.delay(request.proj_name)
        
        return {
            "status": "processing",
            "task_id": task.id,
            "project": request.proj_name,
            "message": "Repository parsing started"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start parsing: {str(e)}")


@router.post("/generate-docs-async")
def generate_docs_async(request: RepoNameRequest):
    """
    Async endpoint to generate documentation
    Returns task ID for status tracking
    """
    try:
        task = generate_documentation_task.delay(request.proj_name)
        
        return {
            "status": "processing",
            "task_id": task.id,
            "project": request.proj_name,
            "message": "Documentation generation started"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start doc generation: {str(e)}")


@router.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    """
    Get the status and result of a Celery task
    """
    try:
        from backend.celery_config import app
        
        task_result = app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
        }
        
        if task_result.status == "PENDING":
            response["message"] = "Task is waiting to be processed"
        elif task_result.status == "STARTED":
            response["message"] = "Task has started"
        elif task_result.status == "SUCCESS":
            response["result"] = task_result.result
            response["message"] = "Task completed successfully"
        elif task_result.status == "FAILURE":
            response["error"] = str(task_result.info)
            response["message"] = "Task failed"
        elif task_result.status == "RETRY":
            response["message"] = "Task is being retried"
        elif task_result.status == "REVOKED":
            response["message"] = "Task was revoked"
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/tasks")
def get_all_tasks():
    """
    Get stats about all active and recent tasks
    """
    try:
        from backend.celery_config import app
        from celery.app.control import Inspect
        
        insp = Inspect(app=app)
        
        return {
            "active": insp.active(),
            "scheduled": insp.scheduled(),
            "reserved": insp.reserved(),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks info: {str(e)}")


# ===== DOCUMENTATION RETRIEVAL ENDPOINTS =====

@router.get("/documentation/{proj_name}")
def get_project_documentation(proj_name: str):
    """
    Retrieve generated documentation for a specific project
    
    Args:
        proj_name: The project name to retrieve documentation for
        
    Returns:
        Documentation record with content, repo URL, and generation timestamp
    """
    try:
        result = get_documentation_by_project(proj_name)
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No documentation found for project: {proj_name}"
            )
        
        doc_record = result.data[0]
        
        return {
            "status": "success",
            "project": proj_name,
            "documentation": {
                "id": doc_record.get("id"),
                "content": doc_record.get("content"),
                "repo_url": doc_record.get("repo_url"),
                "generated_at": doc_record.get("generated_at"),
                "status": doc_record.get("status")
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documentation: {str(e)}"
        )


@router.get("/documentation/{proj_name}/markdown")
def get_project_documentation_markdown(proj_name: str):
    """
    Retrieve documentation for a specific project as markdown
    
    Returns the raw markdown content with Content-Type: text/markdown
    Useful for displaying in frontend or downloading
    """
    try:
        result = get_documentation_by_project(proj_name)
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No documentation found for project: {proj_name}"
            )
        
        doc_record = result.data[0]
        content = doc_record.get("content", "")
        
        # Return markdown content with appropriate header
        return {
            "content": content,
            "content_type": "text/markdown",
            "project": proj_name,
            "generated_at": doc_record.get("generated_at")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve markdown: {str(e)}"
        )


@router.get("/documentation")
def get_all_projects_documentation():
    """
    List all documented projects with metadata
    
    Returns a list of projects that have generated documentation,
    ordered by most recent generation first
    """
    try:
        result = get_all_documentation()
        
        if not result.data:
            return {
                "status": "success",
                "total": 0,
                "projects": []
            }
        
        projects = [
            {
                "proj_name": record.get("proj_name"),
                "repo_url": record.get("repo_url"),
                "generated_at": record.get("generated_at"),
                "id": record.get("id")
            }
            for record in result.data
        ]
        
        return {
            "status": "success",
            "total": len(projects),
            "projects": projects
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documentation list: {str(e)}"
        )

