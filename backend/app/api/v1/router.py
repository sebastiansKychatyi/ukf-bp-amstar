from fastapi import APIRouter
from app.api.v1.endpoints import auth, teams, challenges, ratings, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])
