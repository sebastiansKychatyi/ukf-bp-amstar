from fastapi import APIRouter
from app.api.v1.endpoints import auth, teams, challenges, ratings, users, stats, admin
from app.api.v1.endpoints import team_members, join_requests, matchmaking, statistics, notifications, tournaments

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Public platform statistics (landing page counters)
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])

# Team endpoints (CRUD + stats + match history)
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])

# Team membership management (roster, leave, transfer captaincy)
api_router.include_router(team_members.router, prefix="/teams", tags=["team-members"])

# Join requests
api_router.include_router(join_requests.router, prefix="/join-requests", tags=["join-requests"])

api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])

# Player statistics and leaderboards
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])

# Smart Matchmaking Algorithm
api_router.include_router(matchmaking.router, prefix="/matchmaking", tags=["matchmaking"])

# In-app notifications
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Tournaments (League & Knockout)
api_router.include_router(tournaments.router, prefix="/tournaments", tags=["tournaments"])

# Admin panel (superuser only — announcement GET is public)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
