"""
Team Service Layer

Contains all business logic related to teams including:
- Team CRUD with validation
- Team statistics aggregation
- Match history retrieval
- Roster management with player stats
- Ownership verification
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app import crud, models, schemas
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.challenge import Challenge, ChallengeStatus
from app.models.player_statistics import PlayerStatistics
from app.schemas.team import TeamStatsSummary, MatchHistoryItem
from app.schemas.team_member import TeamMemberWithStats
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
    Service class for team-related business logic.

    Encapsulates all business rules and operations related to teams,
    providing a clean separation between the API layer and data access layer.
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.team_crud = crud.team
        self.user_crud = crud.user

    # =========================================================================
    # TEAM RETRIEVAL
    # =========================================================================

    def get_team_by_id(
        self,
        team_id: int,
        eager_load_captain: bool = True
    ) -> models.Team:
        """
        Get team by ID with eager loading of captain and members.

        Args:
            team_id: Team identifier
            eager_load_captain: Whether to eager load captain relationship

        Returns:
            Team model instance

        Raises:
            TeamNotFoundError: If team doesn't exist
        """
        if eager_load_captain:
            team = self.db.query(models.Team)\
                .options(
                    joinedload(models.Team.captain),
                    joinedload(models.Team.members),
                )\
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
    ) -> List[models.Team]:
        """
        Get list of teams with pagination and eager loading.

        Uses joinedload for captain and members to avoid N+1 queries
        and ensure member_count property works correctly.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of team model instances
        """
        teams = self.db.query(models.Team)\
            .options(
                joinedload(models.Team.captain),
                joinedload(models.Team.members),
            )\
            .offset(skip)\
            .limit(limit)\
            .all()

        self._log_operation("Retrieved teams", count=len(teams), skip=skip, limit=limit)
        return teams

    def get_team_count(self) -> int:
        """Get total count of teams."""
        count = self.db.query(func.count(models.Team.id)).scalar()
        return count or 0

    def get_user_team(self, user_id: int) -> Optional[models.Team]:
        """
        Get team owned by a specific captain.

        Args:
            user_id: Captain's user ID

        Returns:
            Team model instance or None if user has no team
        """
        team = self.team_crud.get_by_captain(self.db, captain_id=user_id)

        if team:
            self._log_operation("Retrieved user team", user_id=user_id, team_id=team.id)

        return team

    def get_my_team(self, user_id: int) -> models.Team:
        """
        Get the current user's team (as captain or member).

        Checks captain ownership first, then team membership.

        Args:
            user_id: ID of the current user

        Returns:
            Team model instance with captain info eager-loaded

        Raises:
            TeamNotFoundError: If user is not part of any team
        """
        # Check if user is captain of a team
        team = self.db.query(models.Team)\
            .options(
                joinedload(models.Team.captain),
                joinedload(models.Team.members),
            )\
            .filter(models.Team.captain_id == user_id)\
            .first()

        if not team:
            # Check if user is a member of a team
            membership = self.db.query(TeamMember)\
                .options(
                    joinedload(TeamMember.team).joinedload(models.Team.captain),
                )\
                .filter(TeamMember.user_id == user_id)\
                .first()
            if membership:
                team = membership.team

        if not team:
            raise TeamNotFoundError(f"user_{user_id}")

        self._log_operation("Retrieved my team", user_id=user_id, team_id=team.id)
        return team

    # =========================================================================
    # TEAM STATISTICS & MATCH HISTORY
    # =========================================================================

    def get_team_stats(self, team_id: int) -> TeamStatsSummary:
        """
        Get aggregated statistics for a team from completed challenges.

        Computes wins, draws, losses, goals scored/conceded, goal difference,
        and win rate from all completed challenges involving the team.

        Args:
            team_id: Team identifier

        Returns:
            TeamStatsSummary with aggregated statistics

        Raises:
            TeamNotFoundError: If team doesn't exist
        """
        self.get_team_by_id(team_id, eager_load_captain=False)

        challenges = self.db.query(Challenge).filter(
            Challenge.status == ChallengeStatus.COMPLETED,
            or_(
                Challenge.challenger_id == team_id,
                Challenge.opponent_id == team_id,
            ),
        ).all()

        wins = draws = losses = goals_scored = goals_conceded = 0

        for c in challenges:
            if c.challenger_score is None or c.opponent_score is None:
                continue

            if c.challenger_id == team_id:
                team_goals = c.challenger_score
                opp_goals = c.opponent_score
            else:
                team_goals = c.opponent_score
                opp_goals = c.challenger_score

            goals_scored += team_goals
            goals_conceded += opp_goals

            if team_goals > opp_goals:
                wins += 1
            elif team_goals < opp_goals:
                losses += 1
            else:
                draws += 1

        total = wins + draws + losses
        win_rate = round((wins / total) * 100, 1) if total > 0 else 0.0

        self._log_operation("Retrieved team stats", team_id=team_id, total_matches=total)
        return TeamStatsSummary(
            total_matches=total,
            wins=wins,
            draws=draws,
            losses=losses,
            goals_scored=goals_scored,
            goals_conceded=goals_conceded,
            goal_difference=goals_scored - goals_conceded,
            win_rate=win_rate,
        )

    def get_team_match_history(
        self,
        team_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> List[MatchHistoryItem]:
        """
        Get match history for a team (completed and accepted challenges).

        Returns matches ordered by date (most recent first) with opponent info
        and result (W/L/D) for completed matches.

        Args:
            team_id: Team identifier
            skip: Pagination offset
            limit: Maximum number of matches to return

        Returns:
            List of MatchHistoryItem instances

        Raises:
            TeamNotFoundError: If team doesn't exist
        """
        self.get_team_by_id(team_id, eager_load_captain=False)

        challenges = self.db.query(Challenge)\
            .options(
                joinedload(Challenge.challenger),
                joinedload(Challenge.opponent),
            )\
            .filter(
                Challenge.status.in_([ChallengeStatus.COMPLETED, ChallengeStatus.ACCEPTED]),
                or_(
                    Challenge.challenger_id == team_id,
                    Challenge.opponent_id == team_id,
                ),
            )\
            .order_by(Challenge.match_date.desc().nullslast(), Challenge.created_at.desc())\
            .offset(skip).limit(limit)\
            .all()

        history = []
        for c in challenges:
            is_challenger = c.challenger_id == team_id
            opponent = c.opponent if is_challenger else c.challenger
            team_score = c.challenger_score if is_challenger else c.opponent_score
            opp_score = c.opponent_score if is_challenger else c.challenger_score

            result = None
            if c.status == ChallengeStatus.COMPLETED and team_score is not None and opp_score is not None:
                if team_score > opp_score:
                    result = "W"
                elif team_score < opp_score:
                    result = "L"
                else:
                    result = "D"

            history.append(MatchHistoryItem(
                challenge_id=c.id,
                opponent_id=opponent.id,
                opponent_name=opponent.name,
                match_date=c.match_date,
                location=c.location,
                team_score=team_score,
                opponent_score=opp_score,
                result=result,
                status=c.status.value,
            ))

        self._log_operation("Retrieved match history", team_id=team_id, count=len(history))
        return history

    def get_team_roster_with_stats(self, team_id: int) -> List[TeamMemberWithStats]:
        """
        Get team roster with player statistics.

        Uses a batch query for PlayerStatistics to avoid the N+1 problem
        (2 queries total regardless of roster size).

        Args:
            team_id: Team identifier

        Returns:
            List of TeamMemberWithStats instances

        Raises:
            TeamNotFoundError: If team doesn't exist
        """
        self.get_team_by_id(team_id, eager_load_captain=False)

        members = self.db.query(TeamMember)\
            .options(joinedload(TeamMember.user))\
            .filter(TeamMember.team_id == team_id)\
            .all()

        # Batch query for player statistics — fixes N+1
        user_ids = [m.user_id for m in members]
        stats_map: dict = {}
        if user_ids:
            stats_rows = self.db.query(PlayerStatistics)\
                .filter(PlayerStatistics.user_id.in_(user_ids))\
                .all()
            stats_map = {s.user_id: s for s in stats_rows}

        result = []
        for member in members:
            stats = stats_map.get(member.user_id)
            result.append(TeamMemberWithStats(
                id=member.id,
                team_id=member.team_id,
                user_id=member.user_id,
                role=member.role.value,
                position=member.position,
                jersey_number=member.jersey_number,
                joined_at=member.joined_at or member.created_at,
                user={
                    "id": member.user.id,
                    "username": member.user.username,
                    "full_name": member.user.full_name,
                    "email": member.user.email,
                },
                goals=stats.goals if stats else 0,
                assists=stats.assists if stats else 0,
                matches_played=stats.matches_played if stats else 0,
                yellow_cards=stats.yellow_cards if stats else 0,
                red_cards=stats.red_cards if stats else 0,
            ))

        self._log_operation("Retrieved roster with stats", team_id=team_id, count=len(result))
        return result

    # =========================================================================
    # TEAM CRUD OPERATIONS
    # =========================================================================

    def create_team(
        self,
        team_in: schemas.TeamCreate,
        captain_id: int
    ) -> models.Team:
        """
        Create a new team with business rule validation.

        Business Rules:
        - Each captain can only have one team
        - Team name must be unique
        - Captain is automatically added as a team member

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

        # Add captain as team member
        existing_membership = self.db.query(TeamMember)\
            .filter(TeamMember.user_id == captain_id)\
            .first()
        if not existing_membership:
            captain_member = TeamMember(
                team_id=team.id,
                user_id=captain_id,
                role=TeamMemberRole.CAPTAIN,
            )
            self.db.add(captain_member)
            self.db.commit()
            self.db.refresh(team)

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
        Update team with ownership verification.

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
        team = self.get_team_by_id(team_id, eager_load_captain=False)

        if team.captain_id != current_user_id:
            self._log_error(
                "update_team",
                NotTeamOwnerError(),
                team_id=team_id,
                captain_id=team.captain_id,
                user_id=current_user_id
            )
            raise NotTeamOwnerError()

        if team_in.name and team_in.name != team.name:
            existing_name = self.team_crud.get_by_name(self.db, name=team_in.name)
            if existing_name:
                raise TeamNameAlreadyExistsError(team_in.name)

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
        Delete team with ownership verification.

        Business Rules:
        - Only team captain can delete team

        Args:
            team_id: ID of team to delete
            current_user_id: ID of user making the request

        Returns:
            Deleted team model instance

        Raises:
            TeamNotFoundError: If team doesn't exist
            NotTeamOwnerError: If user is not the team captain
        """
        team = self.get_team_by_id(team_id, eager_load_captain=False)

        if team.captain_id != current_user_id:
            self._log_error(
                "delete_team",
                NotTeamOwnerError(),
                team_id=team_id,
                captain_id=team.captain_id,
                user_id=current_user_id
            )
            raise NotTeamOwnerError()

        team = self.team_crud.remove(self.db, id=team_id)

        self._log_operation(
            "Deleted team",
            team_id=team_id,
            user_id=current_user_id
        )

        return team

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def verify_team_ownership(
        self,
        team_id: int,
        user_id: int
    ) -> bool:
        """
        Verify if user owns the specified team.

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
        Search teams by name or description.

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
