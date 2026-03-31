"""
Service layer for team operations including join request/approval flow
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.schemas import (
    JoinRequestCreate,
    JoinRequestReview,
    JoinRequestStatus,
    TeamCreate,
    TeamMemberCreate,
    TeamRole,
    TeamUpdate,
)


class TeamServiceError(Exception):
    """Base exception for team service errors"""
    pass


class TeamNotFoundError(TeamServiceError):
    """Raised when team is not found"""
    pass


class PlayerNotFoundError(TeamServiceError):
    """Raised when player is not found"""
    pass


class InsufficientPermissionsError(TeamServiceError):
    """Raised when user lacks required permissions"""
    pass


class DuplicateRequestError(TeamServiceError):
    """Raised when a duplicate join request is created"""
    pass


class TeamFullError(TeamServiceError):
    """Raised when team has reached maximum capacity"""
    pass


class TeamService:
    """Service for managing teams and memberships"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_team(self, team_data: TeamCreate) -> dict:
        """
        Create a new team with the specified player as captain

        Args:
            team_data: Team creation data including captain_id

        Returns:
            Created team data

        Raises:
            PlayerNotFoundError: If captain player doesn't exist
        """
        # Verify captain exists
        captain_query = select(Player).where(
            and_(
                Player.id == team_data.captain_id,
                Player.is_active == True
            )
        )
        captain_result = await self.db.execute(captain_query)
        captain = captain_result.scalar_one_or_none()

        if not captain:
            raise PlayerNotFoundError(f"Player {team_data.captain_id} not found or inactive")

        # Create team
        team_dict = team_data.model_dump(exclude={'captain_id'})
        team = Team(**team_dict)

        self.db.add(team)
        await self.db.flush()  # Get team.id without committing

        # Add captain as team member
        captain_member = TeamMember(
            team_id=team.id,
            player_id=team_data.captain_id,
            role=TeamRole.CAPTAIN,
            is_active=True
        )

        self.db.add(captain_member)
        await self.db.commit()
        await self.db.refresh(team)

        return team

    async def update_team(
        self,
        team_id: UUID,
        team_data: TeamUpdate,
        requesting_player_id: UUID
    ) -> dict:
        """
        Update team information (captain only)

        Args:
            team_id: Team to update
            team_data: Updated team data
            requesting_player_id: Player making the request

        Returns:
            Updated team data

        Raises:
            TeamNotFoundError: If team doesn't exist
            InsufficientPermissionsError: If player is not a captain
        """
        # Verify team exists
        team = await self._get_team(team_id)

        # Verify requester is captain
        await self._verify_captain(team_id, requesting_player_id)

        # Update team
        update_data = team_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)

        await self.db.commit()
        await self.db.refresh(team)

        return team

    async def create_join_request(
        self,
        request_data: JoinRequestCreate
    ) -> dict:
        """
        Create a request for a player to join a team

        Args:
            request_data: Join request data

        Returns:
            Created join request

        Raises:
            TeamNotFoundError: If team doesn't exist
            PlayerNotFoundError: If player doesn't exist
            DuplicateRequestError: If pending request already exists
            TeamFullError: If team has reached max capacity
        """
        # Verify team exists and is recruiting
        team = await self._get_team(request_data.team_id)

        if not team.is_recruiting:
            raise TeamServiceError("Team is not currently recruiting")

        # Verify player exists
        player = await self._get_player(request_data.player_id)

        # Check if player is already a member
        existing_member = await self._get_team_member(
            request_data.team_id,
            request_data.player_id
        )

        if existing_member and existing_member.is_active:
            raise DuplicateRequestError("Player is already a member of this team")

        # Check for pending request
        pending_query = select(TeamJoinRequest).where(
            and_(
                TeamJoinRequest.team_id == request_data.team_id,
                TeamJoinRequest.player_id == request_data.player_id,
                TeamJoinRequest.status == JoinRequestStatus.PENDING
            )
        )
        pending_result = await self.db.execute(pending_query)
        pending_request = pending_result.scalar_one_or_none()

        if pending_request:
            raise DuplicateRequestError("A pending join request already exists")

        # Check team capacity
        member_count = await self._get_active_member_count(request_data.team_id)
        if member_count >= team.max_players:
            raise TeamFullError("Team has reached maximum capacity")

        # Create join request
        join_request = TeamJoinRequest(
            team_id=request_data.team_id,
            player_id=request_data.player_id,
            message=request_data.message,
            status=JoinRequestStatus.PENDING
        )

        self.db.add(join_request)
        await self.db.commit()
        await self.db.refresh(join_request)

        return join_request

    async def review_join_request(
        self,
        request_id: UUID,
        review_data: JoinRequestReview,
        reviewing_captain_id: UUID
    ) -> dict:
        """
        Review (approve/reject) a join request

        Args:
            request_id: Join request to review
            review_data: Review decision and message
            reviewing_captain_id: Captain reviewing the request

        Returns:
            Updated join request

        Raises:
            TeamServiceError: If request not found or already reviewed
            InsufficientPermissionsError: If reviewer is not a captain
        """
        # Get join request
        request_query = select(TeamJoinRequest).where(
            TeamJoinRequest.id == request_id
        )
        request_result = await self.db.execute(request_query)
        join_request = request_result.scalar_one_or_none()

        if not join_request:
            raise TeamServiceError("Join request not found")

        if join_request.status != JoinRequestStatus.PENDING:
            raise TeamServiceError("Join request has already been reviewed")

        # Verify reviewer is captain
        await self._verify_captain(join_request.team_id, reviewing_captain_id)

        # If approved, check team capacity again
        if review_data.status == JoinRequestStatus.APPROVED:
            team = await self._get_team(join_request.team_id)
            member_count = await self._get_active_member_count(join_request.team_id)

            if member_count >= team.max_players:
                raise TeamFullError("Team has reached maximum capacity")

            # Create team membership
            team_member = TeamMember(
                team_id=join_request.team_id,
                player_id=join_request.player_id,
                role=TeamRole.MEMBER,
                is_active=True
            )
            self.db.add(team_member)

        # Update join request
        join_request.status = review_data.status
        join_request.reviewed_by = reviewing_captain_id
        join_request.review_message = review_data.review_message
        join_request.reviewed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(join_request)

        return join_request

    async def get_pending_requests(self, team_id: UUID) -> list:
        """
        Get all pending join requests for a team

        Args:
            team_id: Team ID

        Returns:
            List of pending join requests
        """
        query = (
            select(TeamJoinRequest)
            .where(
                and_(
                    TeamJoinRequest.team_id == team_id,
                    TeamJoinRequest.status == JoinRequestStatus.PENDING
                )
            )
            .options(selectinload(TeamJoinRequest.player))
            .order_by(TeamJoinRequest.created_at.desc())
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def remove_team_member(
        self,
        team_id: UUID,
        player_id: UUID,
        requesting_player_id: UUID
    ) -> None:
        """
        Remove a player from a team

        Args:
            team_id: Team ID
            player_id: Player to remove
            requesting_player_id: Player making the request (captain or self)

        Raises:
            InsufficientPermissionsError: If requester is not captain or self
        """
        # Get team member
        team_member = await self._get_team_member(team_id, player_id)

        if not team_member or not team_member.is_active:
            raise TeamServiceError("Player is not an active member of this team")

        # Check permissions: captain or self can remove
        is_captain = await self._is_captain(team_id, requesting_player_id)
        is_self = requesting_player_id == player_id

        if not (is_captain or is_self):
            raise InsufficientPermissionsError(
                "Only team captains or the player themselves can remove membership"
            )

        # Cannot remove if last captain
        if team_member.role == TeamRole.CAPTAIN:
            captain_count_query = select(func.count()).select_from(TeamMember).where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.role == TeamRole.CAPTAIN,
                    TeamMember.is_active == True
                )
            )
            captain_count_result = await self.db.execute(captain_count_query)
            captain_count = captain_count_result.scalar()

            if captain_count <= 1:
                raise TeamServiceError("Cannot remove the last captain from the team")

        # Mark as inactive
        team_member.is_active = False
        team_member.left_at = datetime.utcnow()

        await self.db.commit()

    async def assign_captain(
        self,
        team_id: UUID,
        new_captain_id: UUID,
        requesting_captain_id: UUID
    ) -> None:
        """
        Assign captain role to a team member

        Args:
            team_id: Team ID
            new_captain_id: Player to promote to captain
            requesting_captain_id: Current captain making the request

        Raises:
            InsufficientPermissionsError: If requester is not a captain
        """
        # Verify requester is captain
        await self._verify_captain(team_id, requesting_captain_id)

        # Get new captain's membership
        team_member = await self._get_team_member(team_id, new_captain_id)

        if not team_member or not team_member.is_active:
            raise TeamServiceError("Player is not an active member of this team")

        # Promote to captain
        team_member.role = TeamRole.CAPTAIN

        await self.db.commit()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_team(self, team_id: UUID):
        """Get team or raise exception"""
        query = select(Team).where(
            and_(Team.id == team_id, Team.is_active == True)
        )
        result = await self.db.execute(query)
        team = result.scalar_one_or_none()

        if not team:
            raise TeamNotFoundError(f"Team {team_id} not found")

        return team

    async def _get_player(self, player_id: UUID):
        """Get player or raise exception"""
        query = select(Player).where(
            and_(Player.id == player_id, Player.is_active == True)
        )
        result = await self.db.execute(query)
        player = result.scalar_one_or_none()

        if not player:
            raise PlayerNotFoundError(f"Player {player_id} not found")

        return player

    async def _get_team_member(
        self,
        team_id: UUID,
        player_id: UUID
    ) -> Optional:
        """Get team member relationship"""
        query = select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.player_id == player_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _is_captain(self, team_id: UUID, player_id: UUID) -> bool:
        """Check if player is a captain of the team"""
        query = select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.player_id == player_id,
                TeamMember.role == TeamRole.CAPTAIN,
                TeamMember.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def _verify_captain(self, team_id: UUID, player_id: UUID) -> None:
        """Verify player is captain or raise exception"""
        if not await self._is_captain(team_id, player_id):
            raise InsufficientPermissionsError(
                "Only team captains can perform this action"
            )

    async def _get_active_member_count(self, team_id: UUID) -> int:
        """Get count of active team members"""
        query = select(func.count()).select_from(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar()


# Stub model classes — replace with actual SQLAlchemy model imports:
#   from app.models.team import Team, TeamMember, TeamJoinRequest
#   from app.models.player import Player
class Team:
    pass


class Player:
    pass


class TeamMember:
    pass


class TeamJoinRequest:
    pass
