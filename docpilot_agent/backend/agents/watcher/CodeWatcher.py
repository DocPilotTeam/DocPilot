from fastapi import APIRouter 
from git import Repo

router=APIRouter()
@router.get("/getChangedFiles")
def codeWatcher(projUrl:str):
    repo=Repo(projUrl)
    files=repo.git.diff("--name-only","HEAD~1","HEAD")
    final_list=files.split("\n")
    print(final_list)
    return {"changed_Files":final_list}