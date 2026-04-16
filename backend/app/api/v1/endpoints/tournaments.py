"""
Tournament API Endpoints

Full lifecycle management: create, register teams, start, record results,
view standings / bracket.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, get_current_captain, allow_captain_or_referee
from app.models.user import User
from app.models.tournament import TournamentStatus, TournamentType
from app.services.tournament_service import TournamentService
from app.services.elo_service import EloService
from app.schemas.tournament import (
    TournamentCreate,
    TournamentUpdate,
    TournamentJoin,
    MatchResultSubmit,
    TournamentResponse,
    TournamentDetailResponse,
    TournamentListResponse,
    TournamentMatchResponse,
    ParticipantResponse,
    StandingsResponse,
    BracketResponse,
    BracketRound,
    EloUpdateInfo,
    MatchResultResponse,
)
from app.core.exceptions import (
    TournamentNotFoundError,
    TournamentNameAlreadyExistsError,
    TournamentFullError,
    TeamAlreadyInTournamentError,
    InvalidTournamentStatusError,
    TournamentNotEnoughTeamsError,
    TeamNotFoundError,
    InsufficientPermissionsError,
    AmStarException,
)

router = APIRouter()


# Exception to HTTP status mapping

def _handle(exc: Exception):
    """Map domain exceptions to HTTP responses."""
    if isinstance(exc, TournamentNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, TeamNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, TournamentNameAlreadyExistsError):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message)
    if isinstance(exc, (TournamentFullError, TeamAlreadyInTournamentError)):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message)
    if isinstance(exc, InvalidTournamentStatusError):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message)
    if isinstance(exc, TournamentNotEnoughTeamsError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message)
    if isinstance(exc, InsufficientPermissionsError):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, AmStarException):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message)
    raise exc


# Build match response with scores from linked challenge

def _match_response(m) -> dict:
    """Build a TournamentMatchResponse dict, pulling scores from Challenge."""
    data = {
        "id": m.id,
        "tournament_id": m.tournament_id,
        "challenge_id": m.challenge_id,
        "round_number": m.round_number,
        "match_order": m.match_order,
        "home_team_id": m.home_team_id,
        "away_team_id": m.away_team_id,
        "winner_team_id": m.winner_team_id,
        "home_team": m.home_team,
        "away_team": m.away_team,
        "winner": m.winner,
        "home_score": None,
        "away_score": None,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
    }
    if m.challenge:
        data["home_score"] = m.challenge.challenger_score
        data["away_score"] = m.challenge.opponent_score
    return data


# List and detail endpoints

@router.get(
    "/",
    response_model=TournamentListResponse,
    summary="List all tournaments",
)
def list_tournaments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    """Get paginated list of tournaments with optional status filter."""
    svc = TournamentService(db)

    parsed_status = None
    if status_filter:
        try:
            parsed_status = TournamentStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    items, total = svc.get_tournaments(skip=skip, limit=limit, status=parsed_status)
    return TournamentListResponse(
        items=[TournamentResponse.model_validate(t) for t in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{tournament_id}",
    response_model=TournamentDetailResponse,
    summary="Get tournament details with participants and matches",
)
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """Get full tournament details including participants, standings, and matches."""
    svc = TournamentService(db)
    try:
        tournament = svc.get_tournament(tournament_id)
    except TournamentNotFoundError as e:
        _handle(e)

    # Build match responses with scores
    match_responses = [
        TournamentMatchResponse.model_validate(_match_response(m))
        for m in tournament.matches
    ]

    resp = TournamentDetailResponse.model_validate(tournament)
    resp.matches = match_responses
    return resp


# Standings and bracket

@router.get(
    "/{tournament_id}/standings",
    response_model=StandingsResponse,
    summary="Get tournament standings table",
)
def get_standings(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns league table sorted by Points > Goal Difference > Goals Scored.
    """
    svc = TournamentService(db)
    try:
        tournament = svc.get_tournament(tournament_id)
        standings = svc.get_standings(tournament_id)
    except TournamentNotFoundError as e:
        _handle(e)

    return StandingsResponse(
        tournament_id=tournament.id,
        tournament_name=tournament.name,
        standings=[ParticipantResponse.model_validate(p) for p in standings],
    )


@router.get(
    "/{tournament_id}/bracket",
    response_model=BracketResponse,
    summary="Get knockout bracket",
)
def get_bracket(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """Returns the full knockout bracket grouped by rounds."""
    svc = TournamentService(db)
    try:
        tournament = svc.get_tournament(tournament_id)
        rounds_data = svc.get_bracket(tournament_id)
    except TournamentNotFoundError as e:
        _handle(e)

    bracket_rounds = []
    for rd in rounds_data:
        bracket_rounds.append(
            BracketRound(
                round_number=rd["round_number"],
                round_name=rd["round_name"],
                matches=[
                    TournamentMatchResponse.model_validate(_match_response(m))
                    for m in rd["matches"]
                ],
            )
        )

    total_rounds = max(r["round_number"] for r in rounds_data) if rounds_data else 0

    return BracketResponse(
        tournament_id=tournament.id,
        tournament_name=tournament.name,
        total_rounds=total_rounds,
        rounds=bracket_rounds,
    )


# CRUD operations

@router.post(
    "/",
    response_model=TournamentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tournament (captain or referee)",
)
def create_tournament(
    payload: TournamentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_captain_or_referee),
):
    """Create a tournament. Captains and referees can organise."""
    svc = TournamentService(db)
    try:
        tournament = svc.create_tournament(
            user_id=current_user.id,
            name=payload.name,
            type=payload.type,
            max_teams=payload.max_teams,
            description=payload.description,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
    except TournamentNameAlreadyExistsError as e:
        _handle(e)
    return TournamentResponse.model_validate(tournament)


@router.put(
    "/{tournament_id}",
    response_model=TournamentResponse,
    summary="Update tournament details",
)
def update_tournament(
    tournament_id: int,
    payload: TournamentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update tournament. Only the organiser, only in DRAFT/REGISTRATION."""
    svc = TournamentService(db)
    try:
        tournament = svc.update_tournament(
            tournament_id=tournament_id,
            user_id=current_user.id,
            **payload.model_dump(exclude_unset=True),
        )
    except (TournamentNotFoundError, TournamentNameAlreadyExistsError,
            InvalidTournamentStatusError, InsufficientPermissionsError) as e:
        _handle(e)
    return TournamentResponse.model_validate(tournament)


@router.delete(
    "/{tournament_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tournament",
)
def delete_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete tournament. Only the organiser, only in DRAFT/CANCELLED."""
    svc = TournamentService(db)
    try:
        svc.delete_tournament(tournament_id, current_user.id)
    except (TournamentNotFoundError, InvalidTournamentStatusError,
            InsufficientPermissionsError) as e:
        _handle(e)


# Registration

@router.post(
    "/{tournament_id}/open-registration",
    response_model=TournamentResponse,
    summary="Open tournament for team registration",
)
def open_registration(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Transition: DRAFT -> REGISTRATION. Organiser only."""
    svc = TournamentService(db)
    try:
        tournament = svc.open_registration(tournament_id, current_user.id)
    except (TournamentNotFoundError, InvalidTournamentStatusError,
            InsufficientPermissionsError) as e:
        _handle(e)
    return TournamentResponse.model_validate(tournament)


@router.post(
    "/{tournament_id}/join",
    response_model=ParticipantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a team for the tournament",
)
def join_tournament(
    tournament_id: int,
    payload: TournamentJoin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """Captain registers their team. Only during REGISTRATION phase."""
    svc = TournamentService(db)
    try:
        participant = svc.join_tournament(
            tournament_id=tournament_id,
            team_id=payload.team_id,
            user_id=current_user.id,
        )
    except (TournamentNotFoundError, TeamNotFoundError,
            InvalidTournamentStatusError, TournamentFullError,
            TeamAlreadyInTournamentError, InsufficientPermissionsError) as e:
        _handle(e)
    return ParticipantResponse.model_validate(participant)


@router.delete(
    "/{tournament_id}/leave/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Withdraw team from tournament",
)
def leave_tournament(
    tournament_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """Captain withdraws their team. Only during REGISTRATION phase."""
    svc = TournamentService(db)
    try:
        svc.leave_tournament(tournament_id, team_id, current_user.id)
    except (TournamentNotFoundError, TeamNotFoundError,
            InvalidTournamentStatusError, InsufficientPermissionsError) as e:
        _handle(e)


# Start and cancel

@router.post(
    "/{tournament_id}/start",
    response_model=TournamentDetailResponse,
    summary="Start the tournament and generate fixtures",
)
def start_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Transition: REGISTRATION -> ACTIVE.

    Generates all fixtures (round-robin or knockout bracket) and
    notifies all participating teams.
    """
    svc = TournamentService(db)
    try:
        tournament = svc.start_tournament(tournament_id, current_user.id)
    except (TournamentNotFoundError, InvalidTournamentStatusError,
            TournamentNotEnoughTeamsError, InsufficientPermissionsError) as e:
        _handle(e)

    match_responses = [
        TournamentMatchResponse.model_validate(_match_response(m))
        for m in tournament.matches
    ]
    resp = TournamentDetailResponse.model_validate(tournament)
    resp.matches = match_responses
    return resp


@router.post(
    "/{tournament_id}/cancel",
    response_model=TournamentResponse,
    summary="Cancel the tournament",
)
def cancel_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a tournament. Organiser only. Allowed from any non-terminal state."""
    svc = TournamentService(db)
    try:
        tournament = svc.cancel_tournament(tournament_id, current_user.id)
    except (TournamentNotFoundError, InvalidTournamentStatusError,
            InsufficientPermissionsError) as e:
        _handle(e)
    return TournamentResponse.model_validate(tournament)


# Match results

@router.post(
    "/{tournament_id}/matches/{match_id}/result",
    response_model=MatchResultResponse,
    summary="Submit match result",
)
def submit_match_result(
    tournament_id: int,
    match_id: int,
    payload: MatchResultSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record the result for a tournament match.

    - Organiser or captain of either team can submit.
    - Automatically recalculates standings.
    - In knockout mode, advances the winner to the next round.
    - If all matches are done, auto-completes the tournament.
    - Triggers global ELO rating update for both teams.
    """
    svc = TournamentService(db)
    try:
        t_match = svc.record_match_result(
            tournament_id=tournament_id,
            match_id=match_id,
            user_id=current_user.id,
            home_score=payload.home_score,
            away_score=payload.away_score,
        )
    except (TournamentNotFoundError, InvalidTournamentStatusError,
            InsufficientPermissionsError) as e:
        _handle(e)

    # Build the match response dict before any further DB commits
    match_data = _match_response(t_match)

    # Advance winner in knockout
    tournament = svc.get_tournament(tournament_id)
    if tournament.type == TournamentType.KNOCKOUT:
        svc.advance_knockout_winner(tournament_id, match_id)

    # Update global ELO ratings — non-fatal if it fails
    elo_home: EloUpdateInfo | None = None
    elo_away: EloUpdateInfo | None = None
    if t_match.challenge_id:
        try:
            home_elo, away_elo = EloService(db).update_ratings(t_match.challenge_id)
            elo_home = EloUpdateInfo(
                team_id=home_elo.team_id,
                team_name=home_elo.team_name,
                old_rating=home_elo.old_rating,
                new_rating=home_elo.new_rating,
                rating_change=home_elo.rating_change,
            )
            elo_away = EloUpdateInfo(
                team_id=away_elo.team_id,
                team_name=away_elo.team_name,
                old_rating=away_elo.old_rating,
                new_rating=away_elo.new_rating,
                rating_change=away_elo.rating_change,
            )
        except Exception:
            pass  # ELO update failure must not block the result submission

    match_data["elo_home"] = elo_home.model_dump() if elo_home else None
    match_data["elo_away"] = elo_away.model_dump() if elo_away else None
    return MatchResultResponse.model_validate(match_data)
