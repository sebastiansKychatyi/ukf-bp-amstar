from fastapi import APIRouter
from app.api.v1.endpoints import auth, teams, challenges, ratings, users

# Import refactored endpoints
try:
    from app.api.v1.endpoints import teams_refactored
    USE_REFACTORED_TEAMS = True
except ImportError:
    USE_REFACTORED_TEAMS = False

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Use refactored teams endpoint if available, otherwise use original
if USE_REFACTORED_TEAMS:
    api_router.include_router(teams_refactored.router, prefix="/teams", tags=["teams"])
else:
    api_router.include_router(teams.router, prefix="/teams", tags=["teams"])

api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])
