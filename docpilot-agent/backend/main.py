from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import os
from git import Repo
from database.db import user_repo_db


app=FastAPI()

class RepoModal(BaseModel):
    projUrl:str
    BranchName:str
    AuthToken:str|None=None
    ProjName:str

##CLONE OR PULL
@app.post("/getRepo")
def fetchRepo(repository:RepoModal):
    basePath="UserRepos"
    os.makedirs(basePath,exist_ok=True)
    path=os.path.join(basePath,repository.ProjName)
    user_repo_db[repository.ProjName]={
        "repo_url": repository.projUrl,
        "local_path": path,
        "branch": repository.BranchName
        }
    
    try:
        if not os.path.exists(path):
            Repo.clone_from(repository.projUrl,path)
        else:
            repo_obj=Repo(path)
            repo_obj.git.reset('--hard')
            repo_obj.git.clean('-fd')
            repo_obj.remotes.origin.pull()
            print(f"Repository Updated to the file==>{path}")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Git operation failed{str(e)}"
        )
    return {"message":"project cloned successfull"}


##CODE WATCHER
@app.get("/getChangedFiles")
def codeWatcher(projUrl:str):
    repo=Repo(projUrl)
    files=repo.git.diff("--name-only","HEAD~1","HEAD")
    final_list=files.split("\n")
    print(final_list)
    return {"changed_Files":final_list}