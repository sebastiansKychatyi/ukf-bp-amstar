from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_challenges():
    return {"message": "Get all challenges"}


@router.get("/{challenge_id}")
def get_challenge(challenge_id: int):
    return {"message": f"Get challenge {challenge_id}"}
