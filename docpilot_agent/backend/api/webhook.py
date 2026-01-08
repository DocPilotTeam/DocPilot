from fastapi import Request,HTTPException,Header,APIRouter

router=APIRouter()


@router.post("/webhook")
async def webhook(
        request:Request,
        x_github_event:str=Header(None,alias="x-github-event")
):
    payload=await request.json()
    headers=request.headers
    print(headers)
    print(f"Received event:{x_github_event}")
    # print(payload)
    print("=================================")
    print(f"CommitID:{payload['after']}")
    if x_github_event == "push":
        print("New push detected!")
    elif x_github_event=="pull":
        print("Pull request Detected")

    return {"message":"success"}