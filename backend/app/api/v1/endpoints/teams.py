from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_teams():
    return {"message": "Get all teams"}


@router.get("/{team_id}")
def get_team(team_id: int):
    return {"message": f"Get team {team_id}"}
