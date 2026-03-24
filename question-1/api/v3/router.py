from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_agent_page():
    return {"message": "Phase 3 Agent Frontend"}
