from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    def get_by_captain(self, db: Session, *, captain_id: int) -> Optional[Team]:
        """Get team by captain ID"""
        return db.query(Team).filter(Team.captain_id == captain_id).first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Team]:
        """Get team by name"""
        return db.query(Team).filter(Team.name == name).first()

    def create_with_captain(self, db: Session, *, obj_in: TeamCreate, captain_id: int) -> Team:
        """Create a team with the specified captain"""
        founded_date = None
        if hasattr(obj_in, 'founded_year') and obj_in.founded_year:
            founded_date = datetime(obj_in.founded_year, 1, 1)

        db_obj = Team(
            name=obj_in.name,
            description=getattr(obj_in, 'description', None),
            city=obj_in.city,
            captain_id=captain_id,
            rating=getattr(obj_in, 'rating_score', 1000),
            founded_date=founded_date,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


team = CRUDTeam(Team)
