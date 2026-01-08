from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import os
from git import Repo
from backend.db.data import user_repo_db
from backend.db.repo_queries import get_repo_by_url, insert_repo

app=FastAPI()

class RepoModal(BaseModel):
    projUrl:str
    BranchName:str
    AuthToken:str|None=None
    ProjName:str

##CLONE OR PULL
@app.post("/getRepo")
def fetchRepo(repository: RepoModal):
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
    )
    basePath = os.path.join(BASE_DIR, "UserRepos")
    os.makedirs(basePath, exist_ok=True)
    print(f"[CloneAgent] Using basePath: {basePath}")
    path = os.path.join(basePath, repository.ProjName)
    # Check if repo already exists in DB
    existing = get_repo_by_url(repository.projUrl)
    # Clone or pull repo
    try:
        if not os.path.exists(path):
            Repo.clone_from(repository.projUrl, path)
        else:
            repo_obj = Repo(path)
            repo_obj.git.reset("--hard")
            repo_obj.git.clean("-fd")
            repo_obj.remotes.origin.pull()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Git operation failed: {str(e)}")
    # Insert only if not exists
    doesExists=False #flag to check if already exists in supabase
    if len(existing.data) == 0:
        insert_repo(
            proj_name=repository.ProjName,
            repo_url=repository.projUrl,
            branch=repository.BranchName,
            auth_token=repository.AuthToken
        )
    else:
        print("Repo already exists in Supabase, skipping insert.")
        doesExists=True

    #Store in-memory for parser
    user_repo_db[repository.ProjName] = {
        "local_path": path,
        "repo_url": repository.projUrl,
        "branch": repository.BranchName,
        "auth_token": repository.AuthToken
    }
    if not doesExists:
        print(f"[Memory] Saved {repository.ProjName} in user_repo_db")
        return {"message": "Project cloned & stored in supabase successfully"}
    else:
        return {"message": "Project pulled & already exists in Supabase"}