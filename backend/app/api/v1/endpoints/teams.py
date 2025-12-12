from fastapi import APIRouter
from typing import List
from app.schemas.team import Team

router = APIRouter()

# Mock team data for initial setup
MOCK_TEAMS = [
    Team(
        id=1,
        name="FC Barcelona Amateur",
        city="Barcelona",
        rating_score=1850,
        description="Amateur football team from Barcelona",
        founded_year=2018,
        logo_url=None,
        created_at="2024-01-15T10:00:00",
        updated_at="2024-01-15T10:00:00"
    ),
    Team(
        id=2,
        name="Madrid Warriors",
        city="Madrid",
        rating_score=1720,
        description="Competitive amateur team from Madrid",
        founded_year=2019,
        logo_url=None,
        created_at="2024-02-20T14:30:00",
        updated_at="2024-02-20T14:30:00"
    ),
    Team(
        id=3,
        name="Valencia United",
        city="Valencia",
        rating_score=1650,
        description="Local amateur football club",
        founded_year=2020,
        logo_url=None,
        created_at="2024-03-10T09:15:00",
        updated_at="2024-03-10T09:15:00"
    ),
    Team(
        id=4,
        name="Sevilla Stars",
        city="Sevilla",
        rating_score=1580,
        description="Rising amateur team from Sevilla",
        founded_year=2021,
        logo_url=None,
        created_at="2024-04-05T16:45:00",
        updated_at="2024-04-05T16:45:00"
    )
]


@router.get("/", response_model=List[Team])
def get_teams():
    """
    Get all teams (mock data for initial setup).

    Returns a list of amateur football teams with their basic information.
    """
    return MOCK_TEAMS


@router.get("/{team_id}", response_model=Team)
def get_team(team_id: int):
    """
    Get a specific team by ID (mock data for initial setup).

    Args:
        team_id: The ID of the team to retrieve

    Returns:
        Team information if found, otherwise returns the first team
    """
    for team in MOCK_TEAMS:
        if team.id == team_id:
            return team
    # Return first team if ID not found (for demo purposes)
    return MOCK_TEAMS[0] if MOCK_TEAMS else None
