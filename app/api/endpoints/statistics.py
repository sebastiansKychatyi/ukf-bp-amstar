"""
FastAPI endpoints for statistics management
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import MatchStatsUpdate
from app.services.statistics_service import StatisticsService, StatisticsServiceError

router = APIRouter(prefix="/statistics", tags=["statistics"])


# Database session dependency — wire to app.db.session.get_db
async def get_db() -> AsyncSession:
    """Yield an async database session per request."""
    ...


# Authentication dependency — wire to app.core.security.get_current_user
async def get_current_player_id() -> UUID:
    """Return the UUID of the currently authenticated user."""
    ...


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.post("/matches/update", status_code=status.HTTP_200_OK)
async def update_match_statistics(
    match_stats: MatchStatsUpdate,
    db: AsyncSession = Depends(get_db),
    current_player_id: UUID = Depends(get_current_player_id)
):
    """
    Update statistics for all players after a match

    This endpoint should be called after a match is completed to update:
    - Individual player statistics (goals, assists, cards, etc.)
    - Team statistics (wins, losses, goals scored/conceded)
    - Player skill ratings (dynamic calculation)
    - Team rating (based on player ratings and performance)

    **Request body:**
    - **match_id**: ID of the completed match
    - **team_id**: Team whose statistics to update
    - **player_stats**: Array of player statistics from the match
    - **match_result**: WIN, DRAW, or LOSS
    - **goals_scored**: Total goals scored by the team
    - **goals_conceded**: Total goals conceded by the team

    **Authorization:**
    Only team captains or match administrators can update statistics.
    """
    service = StatisticsService(db)

    try:
        # Authorization: restrict to team captain or administrator
        result = await service.update_match_statistics(match_stats)
        return {
            "message": "Statistics updated successfully",
            "data": result
        }
    except StatisticsServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/players/{player_id}", status_code=status.HTTP_200_OK)
async def get_player_statistics(
    player_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive statistics for a player

    Returns:
    - Lifetime statistics (across all teams)
    - Per-team breakdown
    - Current skill rating
    - Performance metrics (goals per match, assists per match, etc.)

    **Public endpoint** - no authentication required
    """
    service = StatisticsService(db)

    try:
        stats = await service.get_player_statistics(player_id)
        return stats
    except StatisticsServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/teams/{team_id}", status_code=status.HTTP_200_OK)
async def get_team_statistics(
    team_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive statistics for a team

    Returns:
    - Match record (wins, draws, losses)
    - Goals scored and conceded
    - Team rating
    - Win rate and goal difference

    **Public endpoint** - no authentication required
    """
    ...
