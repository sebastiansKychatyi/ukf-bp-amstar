from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_captain, get_current_active_user
from app.crud.team import team as crud_team
from app.schemas.team import Team, TeamCreate, TeamUpdate
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Team])
def get_teams(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all teams.

    Available to all authenticated users.
    """
    teams = crud_team.get_multi(db, skip=skip, limit=limit)
    return teams


@router.get("/{team_id}", response_model=Team)
def get_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific team by ID.

    Available to all authenticated users.
    """
    team = crud_team.get(db, id=team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team


@router.post("/", response_model=Team, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain)
):
    """
    Create a new team.

    **CAPTAIN role required.**
    Each captain can only create ONE team.
    """
    # Check if captain already has a team
    existing_team = crud_team.get_by_captain(db, captain_id=current_user.id)
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a team. Each captain can only own one team."
        )

    # Check if team name is already taken
    existing_name = crud_team.get_by_name(db, name=team_in.name)
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already taken"
        )

    team = crud_team.create_with_captain(db, obj_in=team_in, captain_id=current_user.id)
    return team


@router.put("/{team_id}", response_model=Team)
def update_team(
    team_id: int,
    team_in: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain)
):
    """
    Update a team.

    **CAPTAIN role required** and you must be the captain of this team.
    """
    team = crud_team.get(db, id=team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Verify ownership
    if team.captain_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own team"
        )

    team = crud_team.update(db, db_obj=team, obj_in=team_in)
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain)
):
    """
    Delete a team.

    **CAPTAIN role required** and you must be the captain of this team.
    """
    team = crud_team.get(db, id=team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Verify ownership
    if team.captain_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own team"
        )

    crud_team.remove(db, id=team_id)
    return None


@router.get("/my/team", response_model=Team)
def get_my_team(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current user's team (if they are a captain).

    Returns the team owned by the current captain, or 404 if they don't have a team.
    """
    team = crud_team.get_by_captain(db, captain_id=current_user.id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a team yet"
        )
    return team
