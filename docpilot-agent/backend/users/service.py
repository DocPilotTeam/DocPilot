from fastapi import APIRouter,Depends
from backend.core.auth_dependency import get_current_user

router=APIRouter()

@router.get("/me")
def me(user_id=Depends(get_current_user)):
    return{"user_id":user_id}