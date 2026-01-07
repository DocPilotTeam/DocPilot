from fastapi import FastAPI,HTTPException,APIRouter
from pydantic import BaseModel
import os
from git import Repo
from backend.db.data import user_repo_db
from backend.api.webhook import router as web_hook
from backend.api.api_routes import router as parser_api_router
from backend.agents.kg_builder.openAiKG import router as cypher_test
from backend.db.repo_queries import get_repo_by_url, insert_repo
# from backend.agents.parser.parser_manager import ParserManager
from backend.agents.watcher.CodeWatcher import router as watch_router
from backend.agents.kg_builder.Kg_reader import router as test_router
from backend.api.api_routes import do_gen_router as documentation_endpoint
from backend.auth.router import router as authentication_router
from backend.repositories.router import router as repositories_router
from fastapi import Depends
from backend.core.auth_dependency import get_current_user


app=FastAPI()

class RepoModal(BaseModel):
    projUrl: str
    BranchName: str
    ProjName: str


@app.post("/getRepo")
def fetchRepo(
    repository: RepoModal,
    user=Depends(get_current_user)  
):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    basePath = os.path.join(BASE_DIR, "UserRepos")
    os.makedirs(basePath, exist_ok=True)

    path = os.path.join(basePath, repository.ProjName)

    github_token = user.get("github_token")
    if not github_token:
        raise HTTPException(status_code=401, detail="GitHub token missing")

    clone_url = repository.projUrl

    if clone_url.startswith("https://"):
        clone_url = clone_url.replace(
            "https://",
            f"https://{github_token}@"
        )

    existing = get_repo_by_url(repository.projUrl)

    try:
        if not os.path.exists(path):
            Repo.clone_from(clone_url, path, branch=repository.BranchName)
        else:
            repo_obj = Repo(path)
            repo_obj.git.reset("--hard")
            repo_obj.git.clean("-fd")
            repo_obj.remotes.origin.pull()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(existing.data) == 0:
        insert_repo(
            proj_name=repository.ProjName,
            repo_url=repository.projUrl,
            branch=repository.BranchName,
            auth_token="stored_in_jwt"
        )

    user_repo_db[repository.ProjName] = {
        "local_path": path,
        "repo_url": repository.projUrl,
        "branch": repository.BranchName
    }

    return {"message": "Repository processed successfully"}


##CODE WATCHER
app.include_router(watch_router,prefix="/api")

##WebHook
app.include_router(web_hook,prefix="/api")

##CODE PARSER
# Register the API routes
app.include_router(parser_api_router, prefix="/api")
app.include_router(cypher_test,prefix="/api")

app.include_router(test_router,prefix="/api")

#DocGen Router
app.include_router(documentation_endpoint,prefix="/api")



app.include_router(authentication_router)

app.include_router(repositories_router,prefix="/api")