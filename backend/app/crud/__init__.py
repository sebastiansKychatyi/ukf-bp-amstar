"""
CRUD operations for AmStar Football Platform
"""

from app.crud.base import CRUDBase
from app.crud.user import CRUDUser, user
from app.crud.team import CRUDTeam, team

__all__ = [
    "CRUDBase",
    "CRUDUser",
    "user",
    "CRUDTeam",
    "team",
]
