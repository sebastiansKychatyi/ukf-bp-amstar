"""
Team Member Service Layer

Contains all business logic related to team membership including:
- Join requests management
- Member roster management
- Role management within teams
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app import models
from app.models.team_member import TeamMemberRole
from app.models.join_request import JoinRequestStatus
from app.models.notification import NotificationType
from app.services.base import BaseService
from app.services.notification_service import NotificationService
from app.core.exceptions import (
    TeamNotFoundError,
    UserNotFoundError,
    NotTeamOwnerError,
    PlayerAlreadyInTeamError,
    PlayerNotInTeamError,
    JoinRequestNotFoundError,
    JoinRequestAlreadyExistsError,
    InvalidJoinRequestStatusError,
    CannotRemoveCaptainError,
    InsufficientPermissionsError,
)


class TeamMemberService(BaseService[models.TeamMember]):
    """
    Service class for team membership business logic

    Handles:
    - Join request creation and review
    - Adding/removing team members
    - Role management (promote to captain, demote)
    - Team roster queries
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self._notifier = NotificationService(db)

    # =========================================================================
    # JOIN REQUEST OPERATIONS
    # =========================================================================

    def create_join_request(
        self,
        team_id: int,
        user_id: int,
        message: Optional[str] = None,
        position: Optional[str] = None
    ) -> models.JoinRequest:
        """
        Create a new join request for a team

        Business Rules:
        - Player cannot be already in a team
        - Player cannot have pending request for same team
        - Team must exist

        Args:
            team_id: ID of the team to join
            user_id: ID of the requesting user
            message: Optional message to captain
            position: Preferred playing position

        Returns:
            Created JoinRequest model

        Raises:
            TeamNotFoundError: If team doesn't exist
            PlayerAlreadyInTeamError: If player is in a team
            JoinRequestAlreadyExistsError: If pending request exists
        """
        # Verify team exists
        team = self.db.query(models.Team).filter(models.Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)

        # Check if player is already in a team
        existing_membership = self.db.query(models.TeamMember).filter(
            models.TeamMember.user_id == user_id
        ).first()
        if existing_membership:
            raise PlayerAlreadyInTeamError(user_id)

        # Check for existing pending request
        existing_request = self.db.query(models.JoinRequest).filter(
            and_(
                models.JoinRequest.team_id == team_id,
                models.JoinRequest.user_id == user_id,
                models.JoinRequest.status == JoinRequestStatus.PENDING
            )
        ).first()
        if existing_request:
            raise JoinRequestAlreadyExistsError(team_id)

        # Create join request
        join_request = models.JoinRequest(
            team_id=team_id,
            user_id=user_id,
            message=message,
            position=position,
            status=JoinRequestStatus.PENDING
        )

        self.db.add(join_request)
        # Flush so the DB assigns an id before we pass it to notify()
        self.db.flush()

        # Notify team captain about the new join request
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        player_name = user.full_name or user.username if user else "A player"
        self._notifier.notify(
            user_id=team.captain_id,
            type=NotificationType.JOIN_REQUEST_RECEIVED,
            title="New Join Request",
            message=f"{player_name} wants to join {team.name}",
            related_id=join_request.id,
        )

        self.db.commit()

        # Re-query with eager loading so the response serializer never
        # triggers lazy loads on a potentially expired session state.
        join_request = (
            self.db.query(models.JoinRequest)
            .options(
                joinedload(models.JoinRequest.user),
                joinedload(models.JoinRequest.team),
            )
            .filter(models.JoinRequest.id == join_request.id)
            .first()
        )

        self._log_operation(
            "Created join request",
            request_id=join_request.id,
            team_id=team_id,
            user_id=user_id
        )

        return join_request

    def get_pending_requests(
        self,
        team_id: int,
        captain_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[models.JoinRequest]:
        """
        Get pending join requests for a team (captain only)

        Args:
            team_id: ID of the team
            captain_id: ID of the requesting captain (for verification)
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of pending JoinRequest models

        Raises:
            TeamNotFoundError: If team doesn't exist
            NotTeamOwnerError: If user is not the captain
        """
        # Verify team and ownership
        team = self.db.query(models.Team).filter(models.Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)
        if team.captain_id != captain_id:
            raise NotTeamOwnerError()

        requests = self.db.query(models.JoinRequest)\
            .options(joinedload(models.JoinRequest.user))\
            .filter(
                and_(
                    models.JoinRequest.team_id == team_id,
                    models.JoinRequest.status == JoinRequestStatus.PENDING
                )
            )\
            .order_by(models.JoinRequest.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

        return requests

    def get_user_join_requests(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[models.JoinRequest]:
        """
        Get all join requests made by a user

        Args:
            user_id: ID of the user
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of JoinRequest models
        """
        requests = self.db.query(models.JoinRequest)\
            .options(joinedload(models.JoinRequest.team))\
            .filter(models.JoinRequest.user_id == user_id)\
            .order_by(models.JoinRequest.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

        return requests

    def review_join_request(
        self,
        request_id: int,
        captain_id: int,
        status: JoinRequestStatus,
        review_message: Optional[str] = None
    ) -> models.JoinRequest:
        """
        Review (accept/reject) a join request

        Business Rules:
        - Only team captain can review
        - Request must be in PENDING status
        - If accepted, player is added to team

        Args:
            request_id: ID of the join request
            captain_id: ID of the reviewing captain
            status: New status (ACCEPTED or REJECTED)
            review_message: Optional response message

        Returns:
            Updated JoinRequest model

        Raises:
            JoinRequestNotFoundError: If request doesn't exist
            NotTeamOwnerError: If user is not the captain
            InvalidJoinRequestStatusError: If status transition is invalid
        """
        # Get request with team
        request = self.db.query(models.JoinRequest)\
            .options(joinedload(models.JoinRequest.team))\
            .filter(models.JoinRequest.id == request_id)\
            .first()

        if not request:
            raise JoinRequestNotFoundError(request_id)

        # Verify captain ownership
        if request.team.captain_id != captain_id:
            raise NotTeamOwnerError()

        # Verify current status is PENDING
        if request.status != JoinRequestStatus.PENDING:
            raise InvalidJoinRequestStatusError(
                current_status=request.status.value,
                attempted_status=status.value
            )

        # Validate new status
        if status not in [JoinRequestStatus.ACCEPTED, JoinRequestStatus.REJECTED]:
            raise InvalidJoinRequestStatusError(
                current_status=request.status.value,
                attempted_status=status.value
            )

        # Update request
        request.status = status
        request.reviewed_by_id = captain_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.review_message = review_message

        # If accepted, add player to team
        if status == JoinRequestStatus.ACCEPTED:
            # Double-check player is not in another team
            existing_membership = self.db.query(models.TeamMember).filter(
                models.TeamMember.user_id == request.user_id
            ).first()
            if existing_membership:
                raise PlayerAlreadyInTeamError(request.user_id)

            # Create team membership
            membership = models.TeamMember(
                team_id=request.team_id,
                user_id=request.user_id,
                role=TeamMemberRole.PLAYER,
                position=request.position
            )
            self.db.add(membership)

            self._log_operation(
                "Player joined team",
                user_id=request.user_id,
                team_id=request.team_id
            )

        # Notify the requesting player
        if status == JoinRequestStatus.ACCEPTED:
            self._notifier.notify(
                user_id=request.user_id,
                type=NotificationType.JOIN_REQUEST_ACCEPTED,
                title="Request Accepted",
                message=f"You have been accepted into {request.team.name}!",
                related_id=request.id,
            )
        elif status == JoinRequestStatus.REJECTED:
            self._notifier.notify(
                user_id=request.user_id,
                type=NotificationType.JOIN_REQUEST_REJECTED,
                title="Request Rejected",
                message=f"Your request to join {request.team.name} was declined.",
                related_id=request.id,
            )

        self.db.commit()
        self.db.refresh(request)

        self._log_operation(
            "Reviewed join request",
            request_id=request_id,
            status=status.value,
            captain_id=captain_id
        )

        return request

    def cancel_join_request(
        self,
        request_id: int,
        user_id: int
    ) -> models.JoinRequest:
        """
        Cancel a pending join request (by the requesting player)

        Args:
            request_id: ID of the join request
            user_id: ID of the user cancelling

        Returns:
            Updated JoinRequest model

        Raises:
            JoinRequestNotFoundError: If request doesn't exist
            InsufficientPermissionsError: If user is not the requester
            InvalidJoinRequestStatusError: If request is not pending
        """
        request = self.db.query(models.JoinRequest).filter(
            models.JoinRequest.id == request_id
        ).first()

        if not request:
            raise JoinRequestNotFoundError(request_id)

        if request.user_id != user_id:
            raise InsufficientPermissionsError()

        if request.status != JoinRequestStatus.PENDING:
            raise InvalidJoinRequestStatusError(
                current_status=request.status.value,
                attempted_status=JoinRequestStatus.CANCELLED.value
            )

        request.status = JoinRequestStatus.CANCELLED
        self.db.commit()
        self.db.refresh(request)

        self._log_operation(
            "Cancelled join request",
            request_id=request_id,
            user_id=user_id
        )

        return request

    # =========================================================================
    # TEAM ROSTER OPERATIONS
    # =========================================================================

    def get_team_roster(
        self,
        team_id: int
    ) -> List[models.TeamMember]:
        """
        Get all members of a team

        Args:
            team_id: ID of the team

        Returns:
            List of TeamMember models with user info

        Raises:
            TeamNotFoundError: If team doesn't exist
        """
        team = self.db.query(models.Team).filter(models.Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)

        members = self.db.query(models.TeamMember)\
            .options(joinedload(models.TeamMember.user))\
            .filter(models.TeamMember.team_id == team_id)\
            .all()

        return members

    def get_member(
        self,
        team_id: int,
        user_id: int
    ) -> Optional[models.TeamMember]:
        """
        Get a specific team member

        Args:
            team_id: ID of the team
            user_id: ID of the user

        Returns:
            TeamMember model or None
        """
        return self.db.query(models.TeamMember).filter(
            and_(
                models.TeamMember.team_id == team_id,
                models.TeamMember.user_id == user_id
            )
        ).first()

    def remove_member(
        self,
        team_id: int,
        user_id: int,
        captain_id: int
    ) -> models.TeamMember:
        """
        Remove a member from a team

        Business Rules:
        - Only captain can remove members
        - Captain cannot remove themselves (must delete team or transfer)

        Args:
            team_id: ID of the team
            user_id: ID of the member to remove
            captain_id: ID of the requesting captain

        Returns:
            Removed TeamMember model

        Raises:
            TeamNotFoundError: If team doesn't exist
            NotTeamOwnerError: If user is not the captain
            PlayerNotInTeamError: If player is not in the team
            CannotRemoveCaptainError: If trying to remove captain
        """
        # Verify team and ownership
        team = self.db.query(models.Team).filter(models.Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)
        if team.captain_id != captain_id:
            raise NotTeamOwnerError()

        # Cannot remove captain
        if user_id == captain_id:
            raise CannotRemoveCaptainError()

        # Find membership
        membership = self.get_member(team_id, user_id)
        if not membership:
            raise PlayerNotInTeamError(user_id, team_id)

        self.db.delete(membership)
        self.db.commit()

        self._log_operation(
            "Removed team member",
            team_id=team_id,
            user_id=user_id,
            captain_id=captain_id
        )

        return membership

    def leave_team(
        self,
        team_id: int,
        user_id: int
    ) -> models.TeamMember:
        """
        Player leaves a team voluntarily

        Business Rules:
        - Captain cannot leave (must delete team or transfer)

        Args:
            team_id: ID of the team
            user_id: ID of the leaving player

        Returns:
            Removed TeamMember model

        Raises:
            TeamNotFoundError: If team doesn't exist
            PlayerNotInTeamError: If player is not in the team
            CannotRemoveCaptainError: If captain tries to leave
        """
        team = self.db.query(models.Team).filter(models.Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)

        # Captain cannot leave
        if team.captain_id == user_id:
            raise CannotRemoveCaptainError()

        membership = self.get_member(team_id, user_id)
        if not membership:
            raise PlayerNotInTeamError(user_id, team_id)

        self.db.delete(membership)
        self.db.commit()

        self._log_operation(
            "Player left team",
            team_id=team_id,
            user_id=user_id
        )

        return membership

    def update_member(
        self,
        team_id: int,
        user_id: int,
        captain_id: int,
        position: Optional[str] = None,
        jersey_number: Optional[int] = None
    ) -> models.TeamMember:
        """
        Update team member info

        Args:
            team_id: ID of the team
            user_id: ID of the member to update
            captain_id: ID of the requesting captain
            position: New playing position
            jersey_number: New jersey number

        Returns:
            Updated TeamMember model

        Raises:
            TeamNotFoundError: If team doesn't exist
            NotTeamOwnerError: If user is not the captain
            PlayerNotInTeamError: If player is not in the team
        """
        # Verify team and ownership
        team = self.db.query(models.Team).filter(models.Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)
        if team.captain_id != captain_id:
            raise NotTeamOwnerError()

        membership = self.get_member(team_id, user_id)
        if not membership:
            raise PlayerNotInTeamError(user_id, team_id)

        if position is not None:
            membership.position = position
        if jersey_number is not None:
            membership.jersey_number = jersey_number

        self.db.commit()
        self.db.refresh(membership)

        self._log_operation(
            "Updated team member",
            team_id=team_id,
            user_id=user_id
        )

        return membership

    def transfer_captaincy(
        self,
        team_id: int,
        current_captain_id: int,
        new_captain_id: int
    ) -> models.Team:
        """
        Transfer team captaincy to another member

        Business Rules:
        - Only current captain can transfer
        - New captain must be a team member

        Args:
            team_id: ID of the team
            current_captain_id: ID of current captain
            new_captain_id: ID of new captain

        Returns:
            Updated Team model

        Raises:
            TeamNotFoundError: If team doesn't exist
            NotTeamOwnerError: If user is not the captain
            PlayerNotInTeamError: If new captain is not in team
        """
        team = self.db.query(models.Team).filter(models.Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)
        if team.captain_id != current_captain_id:
            raise NotTeamOwnerError()

        # Verify new captain is a team member
        new_captain_membership = self.get_member(team_id, new_captain_id)
        if not new_captain_membership:
            raise PlayerNotInTeamError(new_captain_id, team_id)

        # Update roles
        old_captain_membership = self.get_member(team_id, current_captain_id)
        if old_captain_membership:
            old_captain_membership.role = TeamMemberRole.PLAYER

        new_captain_membership.role = TeamMemberRole.CAPTAIN
        team.captain_id = new_captain_id

        self.db.commit()
        self.db.refresh(team)

        self._log_operation(
            "Transferred captaincy",
            team_id=team_id,
            old_captain_id=current_captain_id,
            new_captain_id=new_captain_id
        )

        return team

    def get_user_team(self, user_id: int) -> Optional[models.Team]:
        """
        Get the team a user belongs to

        Args:
            user_id: ID of the user

        Returns:
            Team model or None if user is not in a team
        """
        membership = self.db.query(models.TeamMember)\
            .options(joinedload(models.TeamMember.team))\
            .filter(models.TeamMember.user_id == user_id)\
            .first()

        return membership.team if membership else None
