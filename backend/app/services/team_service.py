"""
Team Service Layer

Contains all business logic related to teams including:
- Team creation and validation
- Ownership verification
- Team queries with optimization
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app import crud, models, schemas
from app.services.base import BaseService
from app.core.exceptions import (
    TeamNotFoundError,
    CaptainAlreadyHasTeamError,
    NotTeamOwnerError,
    TeamNameAlreadyExistsError,
    InsufficientPermissionsError,
)


class TeamService(BaseService[models.Team]):
    """
    Service class for team-related business logic

    This class encapsulates all business rules and operations related to teams,
    providing a clean separation between API layer and data access layer.
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.team_crud = crud.team
        self.user_crud = crud.user

    def get_team_by_id(
        self,
        team_id: int,
        eager_load_captain: bool = True
    ) -> models.Team:
        """
        Get team by ID with optional eager loading

        Args:
            team_id: Team identifier
            eager_load_captain: Whether to eager load captain relationship

        Returns:
            Team model instance

        Raises:
            TeamNotFoundError: If team doesn't exist
        """
        if eager_load_captain:
            # Optimized query - avoids N+1 problem
            team = self.db.query(models.Team)\
                .options(joinedload(models.Team.captain))\
                .filter(models.Team.id == team_id)\
                .first()
        else:
            team = self.team_crud.get(self.db, id=team_id)

        if not team:
            self._log_error("get_team_by_id", TeamNotFoundError(team_id), team_id=team_id)
            raise TeamNotFoundError(team_id)

        self._log_operation("Retrieved team", team_id=team_id, team_name=team.name)
        return team

    def get_teams(
        self,
        skip: int = 0,
        limit: int = 100,
        eager_load_captain: bool = True
    ) -> List[models.Team]:
        """
        Get list of teams with pagination and optimization

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            eager_load_captain: Whether to eager load captain relationship

        Returns:
            List of team model instances
        """
        if eager_load_captain:
            # Optimized query with eager loading
            teams = self.db.query(models.Team)\
                .options(joinedload(models.Team.captain))\
                .offset(skip)\
                .limit(limit)\
                .all()
        else:
            teams = self.team_crud.get_multi(self.db, skip=skip, limit=limit)

        self._log_operation("Retrieved teams", count=len(teams), skip=skip, limit=limit)
        return teams

    def get_team_count(self) -> int:
        """
        Get total count of teams

        Returns:
            Total number of teams
        """
        count = self.db.query(func.count(models.Team.id)).scalar()
        return count or 0

    def get_user_team(self, user_id: int) -> Optional[models.Team]:
        """
        Get team owned by a specific captain

        Args:
            user_id: Captain's user ID

        Returns:
            Team model instance or None if user has no team
        """
        team = self.team_crud.get_by_captain(self.db, captain_id=user_id)

        if team:
            self._log_operation("Retrieved user team", user_id=user_id, team_id=team.id)

        return team

    def create_team(
        self,
        team_in: schemas.TeamCreate,
        captain_id: int
    ) -> models.Team:
        """
        Create a new team with business rule validation

        Business Rules:
        - Each captain can only have one team
        - Team name must be unique
        - Captain must have CAPTAIN role (enforced by endpoint)

        Args:
            team_in: Team creation data
            captain_id: ID of the captain creating the team

        Returns:
            Created team model instance

        Raises:
            CaptainAlreadyHasTeamError: If captain already has a team
            TeamNameAlreadyExistsError: If team name is taken
        """
        # Business Rule: One team per captain
        existing_team = self.team_crud.get_by_captain(self.db, captain_id=captain_id)
        if existing_team:
            self._log_error(
                "create_team",
                CaptainAlreadyHasTeamError(),
                captain_id=captain_id
            )
            raise CaptainAlreadyHasTeamError()

        # Business Rule: Unique team name
        existing_name = self.team_crud.get_by_name(self.db, name=team_in.name)
        if existing_name:
            self._log_error(
                "create_team",
                TeamNameAlreadyExistsError(team_in.name),
                name=team_in.name
            )
            raise TeamNameAlreadyExistsError(team_in.name)

        # Create team
        team = self.team_crud.create_with_captain(
            self.db,
            obj_in=team_in,
            captain_id=captain_id
        )

        self._log_operation(
            "Created team",
            team_id=team.id,
            team_name=team.name,
            captain_id=captain_id
        )

        return team

    def update_team(
        self,
        team_id: int,
        team_in: schemas.TeamUpdate,
        current_user_id: int
    ) -> models.Team:
        """
        Update team with ownership verification

        Business Rules:
        - Only team captain can update team
        - Team name must remain unique if changed

        Args:
            team_id: ID of team to update
            team_in: Updated team data
            current_user_id: ID of user making the request

        Returns:
            Updated team model instance

        Raises:
            TeamNotFoundError: If team doesn't exist
            NotTeamOwnerError: If user is not the team captain
            TeamNameAlreadyExistsError: If new name is taken
        """
        # Get existing team
        team = self.get_team_by_id(team_id, eager_load_captain=False)

        # Business Rule: Only captain can update
        if team.captain_id != current_user_id:
            self._log_error(
                "update_team",
                NotTeamOwnerError(),
                team_id=team_id,
                captain_id=team.captain_id,
                user_id=current_user_id
            )
            raise NotTeamOwnerError()

        # Business Rule: Unique team name (if changed)
        if team_in.name and team_in.name != team.name:
            existing_name = self.team_crud.get_by_name(self.db, name=team_in.name)
            if existing_name:
                raise TeamNameAlreadyExistsError(team_in.name)

        # Update team
        team = self.team_crud.update(self.db, db_obj=team, obj_in=team_in)

        self._log_operation(
            "Updated team",
            team_id=team.id,
            user_id=current_user_id
        )

        return team

    def delete_team(
        self,
        team_id: int,
        current_user_id: int
    ) -> models.Team:
        """
        Delete team with ownership verification

        Business Rules:
        - Only team captain can delete team
        - Soft delete (can be implemented later)

        Args:
            team_id: ID of team to delete
            current_user_id: ID of user making the request

        Returns:
            Deleted team model instance

        Raises:
            TeamNotFoundError: If team doesn't exist
            NotTeamOwnerError: If user is not the team captain
        """
        # Get existing team
        team = self.get_team_by_id(team_id, eager_load_captain=False)

        # Business Rule: Only captain can delete
        if team.captain_id != current_user_id:
            self._log_error(
                "delete_team",
                NotTeamOwnerError(),
                team_id=team_id,
                captain_id=team.captain_id,
                user_id=current_user_id
            )
            raise NotTeamOwnerError()

        # Delete team
        team = self.team_crud.remove(self.db, id=team_id)

        self._log_operation(
            "Deleted team",
            team_id=team_id,
            user_id=current_user_id
        )

        return team

    def verify_team_ownership(
        self,
        team_id: int,
        user_id: int
    ) -> bool:
        """
        Verify if user owns the specified team

        Args:
            team_id: Team identifier
            user_id: User identifier

        Returns:
            True if user is team captain, False otherwise

        Raises:
            TeamNotFoundError: If team doesn't exist
        """
        team = self.get_team_by_id(team_id, eager_load_captain=False)
        return team.captain_id == user_id

    def search_teams(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Team]:
        """
        Search teams by name or description

        Args:
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching teams
        """
        teams = self.db.query(models.Team)\
            .filter(
                (models.Team.name.ilike(f"%{query}%")) |
                (models.Team.description.ilike(f"%{query}%"))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()

        self._log_operation(
            "Searched teams",
            query=query,
            results=len(teams)
        )

        return teams
