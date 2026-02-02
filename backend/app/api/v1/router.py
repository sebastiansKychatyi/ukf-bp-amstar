from fastapi import APIRouter
from app.api.v1.endpoints import auth, teams, challenges, ratings, users

# Import refactored endpoints
try:
    from app.api.v1.endpoints import teams_refactored
    USE_REFACTORED_TEAMS = True
except ImportError:
    USE_REFACTORED_TEAMS = False

# Import new team management endpoints
from app.api.v1.endpoints import team_members, join_requests

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Use refactored teams endpoint if available, otherwise use original
if USE_REFACTORED_TEAMS:
    api_router.include_router(teams_refactored.router, prefix="/teams", tags=["teams"])
else:
    api_router.include_router(teams.router, prefix="/teams", tags=["teams"])

# Team membership management
api_router.include_router(team_members.router, prefix="/teams", tags=["team-members"])

# Join requests
api_router.include_router(join_requests.router, prefix="/join-requests", tags=["join-requests"])

api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])
