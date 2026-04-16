"""
Tournament Scheduler

Background task that runs every 60 seconds and auto-starts tournaments
whose start_date has arrived and are still in REGISTRATION status.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.tournament import Tournament, TournamentStatus
from app.services.tournament_service import TournamentService
from app.core.exceptions import (
    InvalidTournamentStatusError,
    TournamentNotEnoughTeamsError,
)

logger = logging.getLogger(__name__)


async def _auto_start_tournaments() -> None:
    """Check for tournaments ready to auto-start and start them."""
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        due = (
            db.query(Tournament)
            .filter(
                Tournament.status == TournamentStatus.REGISTRATION,
                Tournament.start_date <= now,
                Tournament.start_date.isnot(None),
            )
            .all()
        )

        for tournament in due:
            try:
                svc = TournamentService(db)
                svc.start_tournament(tournament.id, tournament.created_by_id)
                logger.info(
                    "Auto-started tournament %s (id=%d)",
                    tournament.name,
                    tournament.id,
                )
            except (InvalidTournamentStatusError, TournamentNotEnoughTeamsError) as exc:
                logger.warning(
                    "Could not auto-start tournament %d: %s",
                    tournament.id,
                    exc,
                )
            except Exception:
                logger.exception("Unexpected error auto-starting tournament %d", tournament.id)
    finally:
        db.close()


async def tournament_scheduler_loop() -> None:
    """Infinite loop: check every 60 seconds."""
    logger.info("Tournament auto-start scheduler started")
    while True:
        await asyncio.sleep(60)
        try:
            await _auto_start_tournaments()
        except Exception:
            logger.exception("Error in tournament scheduler loop")
