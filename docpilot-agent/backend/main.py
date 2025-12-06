from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import os
from git import Repo
from db.data import user_repo_db
from api.webhook import router as web_hook
from api.api_routes import router as parser_api_router
from agents.kg_builder.openAiKG import router as cypher_test
from agents.watcher.CodeWatcher import router as watch_router


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
    print(user_repo_db)
    
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
app.include_router(watch_router,prefix="/api")

##WebHook
app.include_router(web_hook,prefix="/api")

##CODE PARSER
# Register the API routes
app.include_router(parser_api_router, prefix="/api")
app.include_router(cypher_test,prefix="/api")