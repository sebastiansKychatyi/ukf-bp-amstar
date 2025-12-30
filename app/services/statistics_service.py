"""
Service layer for updating player and team statistics after matches
"""
from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    EventType,
    MatchEventCreate,
    MatchStatsUpdate,
    PlayerStatsUpdate,
)


class StatisticsServiceError(Exception):
    """Base exception for statistics service errors"""
    pass


class StatisticsService:
    """Service for managing player and team statistics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_match_statistics(
        self,
        match_stats: MatchStatsUpdate
    ) -> dict:
        """
        Update statistics for all players and the team after a match

        This is the main method called after a match is completed. It:
        1. Updates individual player statistics (both team-specific and lifetime)
        2. Updates team statistics
        3. Recalculates player ratings
        4. Recalculates team rating

        Args:
            match_stats: Match statistics including all player stats

        Returns:
            Summary of updated statistics

        Raises:
            StatisticsServiceError: If validation fails
        """
        # Verify team exists
        team = await self._get_team(match_stats.team_id)

        # Track updates for response
        updated_players = []
        events_created = []

        # Process each player's statistics
        for player_stat in match_stats.player_stats:
            # Verify player is team member
            team_member = await self._get_team_member(
                match_stats.team_id,
                player_stat.player_id
            )

            if not team_member or not team_member.is_active:
                raise StatisticsServiceError(
                    f"Player {player_stat.player_id} is not an active member of team {match_stats.team_id}"
                )

            # Update team-specific stats
            await self._update_team_member_stats(team_member, player_stat)

            # Update player's lifetime stats
            await self._update_player_lifetime_stats(player_stat)

            # Create match events for detailed tracking
            events = await self._create_match_events(
                match_stats.match_id,
                match_stats.team_id,
                player_stat
            )
            events_created.extend(events)

            # Recalculate player rating
            new_rating = await self._calculate_player_rating(
                player_stat.player_id,
                match_stats.match_result
            )

            updated_players.append({
                'player_id': player_stat.player_id,
                'new_rating': new_rating
            })

        # Update team statistics
        await self._update_team_statistics(
            match_stats.team_id,
            match_stats.match_result,
            match_stats.goals_scored,
            match_stats.goals_conceded
        )

        # Recalculate team rating
        new_team_rating = await self._calculate_team_rating(match_stats.team_id)

        await self.db.commit()

        return {
            'team_id': match_stats.team_id,
            'match_id': match_stats.match_id,
            'updated_players': updated_players,
            'events_created': len(events_created),
            'new_team_rating': new_team_rating
        }

    async def _update_team_member_stats(
        self,
        team_member,
        player_stat: PlayerStatsUpdate
    ) -> None:
        """Update a team member's statistics"""
        team_member.matches_played += 1
        team_member.goals += player_stat.goals
        team_member.assists += player_stat.assists
        team_member.yellow_cards += player_stat.yellow_cards
        team_member.red_cards += player_stat.red_cards

        if player_stat.clean_sheet:
            team_member.clean_sheets += 1

    async def _update_player_lifetime_stats(
        self,
        player_stat: PlayerStatsUpdate
    ) -> None:
        """Update a player's lifetime statistics"""
        update_stmt = (
            update(Player)
            .where(Player.id == player_stat.player_id)
            .values(
                total_matches_played=Player.total_matches_played + 1,
                total_goals=Player.total_goals + player_stat.goals,
                total_assists=Player.total_assists + player_stat.assists,
                total_yellow_cards=Player.total_yellow_cards + player_stat.yellow_cards,
                total_red_cards=Player.total_red_cards + player_stat.red_cards,
                total_clean_sheets=Player.total_clean_sheets + (1 if player_stat.clean_sheet else 0)
            )
        )
        await self.db.execute(update_stmt)

    async def _create_match_events(
        self,
        match_id: UUID,
        team_id: UUID,
        player_stat: PlayerStatsUpdate
    ) -> List:
        """Create individual match events for tracking"""
        events = []

        # Create goal events
        for _ in range(player_stat.goals):
            event = MatchEvent(
                match_id=match_id,
                team_id=team_id,
                player_id=player_stat.player_id,
                event_type=EventType.GOAL
            )
            self.db.add(event)
            events.append(event)

        # Create assist events
        for _ in range(player_stat.assists):
            event = MatchEvent(
                match_id=match_id,
                team_id=team_id,
                player_id=player_stat.player_id,
                event_type=EventType.ASSIST
            )
            self.db.add(event)
            events.append(event)

        # Create yellow card events
        for _ in range(player_stat.yellow_cards):
            event = MatchEvent(
                match_id=match_id,
                team_id=team_id,
                player_id=player_stat.player_id,
                event_type=EventType.YELLOW_CARD
            )
            self.db.add(event)
            events.append(event)

        # Create red card events
        for _ in range(player_stat.red_cards):
            event = MatchEvent(
                match_id=match_id,
                team_id=team_id,
                player_id=player_stat.player_id,
                event_type=EventType.RED_CARD
            )
            self.db.add(event)
            events.append(event)

        # Create clean sheet event
        if player_stat.clean_sheet:
            event = MatchEvent(
                match_id=match_id,
                team_id=team_id,
                player_id=player_stat.player_id,
                event_type=EventType.CLEAN_SHEET
            )
            self.db.add(event)
            events.append(event)

        return events

    async def _update_team_statistics(
        self,
        team_id: UUID,
        match_result: str,
        goals_scored: int,
        goals_conceded: int
    ) -> None:
        """Update team statistics after a match"""
        updates = {
            'total_matches': Team.total_matches + 1,
            'total_goals_scored': Team.total_goals_scored + goals_scored,
            'total_goals_conceded': Team.total_goals_conceded + goals_conceded
        }

        # Update win/draw/loss counts
        if match_result == 'WIN':
            updates['total_wins'] = Team.total_wins + 1
        elif match_result == 'DRAW':
            updates['total_draws'] = Team.total_draws + 1
        else:  # LOSS
            updates['total_losses'] = Team.total_losses + 1

        update_stmt = (
            update(Team)
            .where(Team.id == team_id)
            .values(**updates)
        )
        await self.db.execute(update_stmt)

    async def _calculate_player_rating(
        self,
        player_id: UUID,
        match_result: str
    ) -> Decimal:
        """
        Calculate updated player rating based on match performance

        Rating Algorithm:
        - Base rating starts at 50.0
        - Performance impacts (per match):
          * Win: +0.5 points
          * Draw: +0.1 points
          * Loss: -0.3 points
          * Goal: +0.8 points
          * Assist: +0.5 points
          * Yellow card: -0.3 points
          * Red card: -1.0 points
          * Clean sheet (GK): +0.6 points

        - Long-term adjustment:
          * Goals/assists per match ratio influences rating
          * Cards per match ratio negatively influences rating
          * Maximum rating: 100.0
          * Minimum rating: 0.0

        Args:
            player_id: Player ID
            match_result: Match result (WIN/DRAW/LOSS)

        Returns:
            New player rating
        """
        # Get player data
        query = select(Player).where(Player.id == player_id)
        result = await self.db.execute(query)
        player = result.scalar_one()

        current_rating = player.skill_rating
        matches_played = player.total_matches_played

        if matches_played == 0:
            return current_rating

        # Calculate performance metrics
        goals_per_match = player.total_goals / matches_played
        assists_per_match = player.total_assists / matches_played
        cards_per_match = (player.total_yellow_cards + player.total_red_cards * 2) / matches_played
        clean_sheets_per_match = player.total_clean_sheets / matches_played

        # Base rating adjustment from match result
        result_adjustment = {
            'WIN': Decimal('0.5'),
            'DRAW': Decimal('0.1'),
            'LOSS': Decimal('-0.3')
        }.get(match_result, Decimal('0.0'))

        # Performance-based adjustment
        performance_score = (
            Decimal(str(goals_per_match)) * Decimal('15.0') +  # Goals heavily weighted
            Decimal(str(assists_per_match)) * Decimal('10.0') +  # Assists moderately weighted
            Decimal(str(clean_sheets_per_match)) * Decimal('8.0') -  # Clean sheets for GKs
            Decimal(str(cards_per_match)) * Decimal('5.0')  # Negative impact of cards
        )

        # Calculate new rating
        # Use exponential moving average to smooth out rating changes
        alpha = Decimal('0.1')  # Learning rate (10% adjustment per match)
        target_rating = Decimal('50.0') + performance_score

        new_rating = current_rating + result_adjustment + (
            alpha * (target_rating - current_rating)
        )

        # Clamp rating between 0 and 100
        new_rating = max(Decimal('0.0'), min(Decimal('100.0'), new_rating))

        # Update player rating
        update_stmt = (
            update(Player)
            .where(Player.id == player_id)
            .values(skill_rating=new_rating)
        )
        await self.db.execute(update_stmt)

        return new_rating

    async def _calculate_team_rating(self, team_id: UUID) -> Decimal:
        """
        Calculate team rating based on:
        1. Average player rating (70% weight)
        2. Win rate (20% weight)
        3. Goal difference per match (10% weight)

        Args:
            team_id: Team ID

        Returns:
            New team rating
        """
        # Get team data
        team = await self._get_team(team_id)

        # Get average player rating for active members
        avg_rating_query = select(
            func.avg(Player.skill_rating)
        ).select_from(
            TeamMember
        ).join(
            Player, TeamMember.player_id == Player.id
        ).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.is_active == True
            )
        )

        result = await self.db.execute(avg_rating_query)
        avg_player_rating = result.scalar() or Decimal('50.0')

        # Calculate win rate component
        if team.total_matches > 0:
            win_rate = Decimal(str(team.total_wins / team.total_matches))
            win_rate_score = win_rate * Decimal('100.0')

            # Calculate goal difference component
            goal_diff = team.total_goals_scored - team.total_goals_conceded
            goal_diff_per_match = Decimal(str(goal_diff / team.total_matches))
            # Normalize goal difference to 0-100 scale (assume +/- 3 goals per match is extreme)
            goal_diff_score = Decimal('50.0') + (goal_diff_per_match * Decimal('16.67'))
            goal_diff_score = max(Decimal('0.0'), min(Decimal('100.0'), goal_diff_score))
        else:
            win_rate_score = Decimal('50.0')
            goal_diff_score = Decimal('50.0')

        # Weighted average
        team_rating = (
            avg_player_rating * Decimal('0.7') +
            win_rate_score * Decimal('0.2') +
            goal_diff_score * Decimal('0.1')
        )

        # Clamp between 0 and 100
        team_rating = max(Decimal('0.0'), min(Decimal('100.0'), team_rating))

        # Update team rating
        update_stmt = (
            update(Team)
            .where(Team.id == team_id)
            .values(team_rating=team_rating)
        )
        await self.db.execute(update_stmt)

        return team_rating

    async def get_player_statistics(self, player_id: UUID) -> dict:
        """
        Get comprehensive statistics for a player

        Args:
            player_id: Player ID

        Returns:
            Player statistics including lifetime and per-team breakdowns
        """
        # Get player lifetime stats
        player_query = select(Player).where(Player.id == player_id)
        player_result = await self.db.execute(player_query)
        player = player_result.scalar_one_or_none()

        if not player:
            raise StatisticsServiceError(f"Player {player_id} not found")

        # Get per-team statistics
        team_stats_query = (
            select(TeamMember, Team)
            .join(Team, TeamMember.team_id == Team.id)
            .where(TeamMember.player_id == player_id)
            .order_by(TeamMember.joined_at.desc())
        )

        team_stats_result = await self.db.execute(team_stats_query)
        team_stats = team_stats_result.all()

        return {
            'player_id': player.id,
            'skill_rating': player.skill_rating,
            'lifetime_stats': {
                'matches_played': player.total_matches_played,
                'goals': player.total_goals,
                'assists': player.total_assists,
                'yellow_cards': player.total_yellow_cards,
                'red_cards': player.total_red_cards,
                'clean_sheets': player.total_clean_sheets,
                'goals_per_match': (
                    player.total_goals / player.total_matches_played
                    if player.total_matches_played > 0 else 0
                ),
                'assists_per_match': (
                    player.total_assists / player.total_matches_played
                    if player.total_matches_played > 0 else 0
                )
            },
            'team_breakdown': [
                {
                    'team_id': tm.team_id,
                    'team_name': team.name,
                    'matches_played': tm.matches_played,
                    'goals': tm.goals,
                    'assists': tm.assists,
                    'yellow_cards': tm.yellow_cards,
                    'red_cards': tm.red_cards,
                    'clean_sheets': tm.clean_sheets,
                    'is_active': tm.is_active
                }
                for tm, team in team_stats
            ]
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_team(self, team_id: UUID):
        """Get team or raise exception"""
        query = select(Team).where(Team.id == team_id)
        result = await self.db.execute(query)
        team = result.scalar_one_or_none()

        if not team:
            raise StatisticsServiceError(f"Team {team_id} not found")

        return team

    async def _get_team_member(self, team_id: UUID, player_id: UUID):
        """Get team member relationship"""
        query = select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.player_id == player_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


# Import from database models - placeholder classes
from sqlalchemy import func


class Team:
    pass


class Player:
    pass


class TeamMember:
    pass


class MatchEvent:
    pass
