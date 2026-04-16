
import math
from itertools import combinations
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.team import Team
from app.models.challenge import Challenge, ChallengeStatus
from app.models.tournament import (
    Tournament,
    TournamentParticipant,
    TournamentMatch,
    TournamentType,
    TournamentStatus,
)
from app.models.notification import NotificationType
from app.services.base import BaseService
from app.services.notification_service import NotificationService
from app.core.exceptions import (
    TournamentNotFoundError,
    TournamentNameAlreadyExistsError,
    TournamentFullError,
    TeamAlreadyInTournamentError,
    InvalidTournamentStatusError,
    TournamentNotEnoughTeamsError,
    TeamNotFoundError,
    InsufficientPermissionsError,
)


# Valid status transitions
_VALID_TRANSITIONS = {
    TournamentStatus.DRAFT: {TournamentStatus.REGISTRATION, TournamentStatus.CANCELLED},
    TournamentStatus.REGISTRATION: {TournamentStatus.ACTIVE, TournamentStatus.CANCELLED},
    TournamentStatus.ACTIVE: {TournamentStatus.COMPLETED, TournamentStatus.CANCELLED},
    TournamentStatus.COMPLETED: set(),
    TournamentStatus.CANCELLED: set(),
}


class TournamentService(BaseService[Tournament]):
    """
    Service implementing tournament lifecycle, fixture generation,
    and standings calculation.
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self._notifier = NotificationService(db)

    # Retrieval

    def get_tournament(self, tournament_id: int) -> Tournament:
        """Get a tournament with participants and matches eagerly loaded."""
        tournament = (
            self.db.query(Tournament)
            .options(
                joinedload(Tournament.participants).joinedload(TournamentParticipant.team),
                joinedload(Tournament.matches).joinedload(TournamentMatch.home_team),
                joinedload(Tournament.matches).joinedload(TournamentMatch.away_team),
                joinedload(Tournament.matches).joinedload(TournamentMatch.winner),
                joinedload(Tournament.matches).joinedload(TournamentMatch.challenge),
                joinedload(Tournament.created_by),
            )
            .filter(Tournament.id == tournament_id)
            .first()
        )
        if not tournament:
            raise TournamentNotFoundError(tournament_id)
        return tournament

    def get_tournaments(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[TournamentStatus] = None,
    ) -> Tuple[List[Tournament], int]:
        """List tournaments with optional status filter. Returns (items, total)."""
        query = self.db.query(Tournament).options(
            joinedload(Tournament.participants),
            joinedload(Tournament.created_by),
        )
        if status:
            query = query.filter(Tournament.status == status)

        total = query.count()
        items = (
            query
            .order_by(Tournament.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    # CRUD operations

    def create_tournament(
        self,
        user_id: int,
        name: str,
        type: str,
        max_teams: int = 8,
        description: Optional[str] = None,
        start_date=None,
        end_date=None,
    ) -> Tournament:
        """
        Create a new tournament in DRAFT status.

        Any authenticated captain or referee can create.
        """
        # Unique name check
        existing = self.db.query(Tournament).filter(Tournament.name == name).first()
        if existing:
            raise TournamentNameAlreadyExistsError(name)

        tournament = Tournament(
            name=name,
            description=description,
            type=TournamentType(type),
            status=TournamentStatus.DRAFT,
            max_teams=max_teams,
            created_by_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        self.db.add(tournament)
        self.db.commit()
        self.db.refresh(tournament)

        self._log_operation("Tournament created", tournament_id=tournament.id, name=name)
        return self.get_tournament(tournament.id)

    def update_tournament(
        self,
        tournament_id: int,
        user_id: int,
        **fields,
    ) -> Tournament:
        """Update tournament details. Only allowed in DRAFT or REGISTRATION."""
        tournament = self.get_tournament(tournament_id)
        self._assert_organiser(tournament, user_id)

        if tournament.status not in (TournamentStatus.DRAFT, TournamentStatus.REGISTRATION):
            raise InvalidTournamentStatusError(
                tournament.status.value, "update tournament"
            )

        # Check name uniqueness if changing
        new_name = fields.get("name")
        if new_name and new_name != tournament.name:
            dup = self.db.query(Tournament).filter(Tournament.name == new_name).first()
            if dup:
                raise TournamentNameAlreadyExistsError(new_name)

        for key, value in fields.items():
            if value is not None and hasattr(tournament, key):
                setattr(tournament, key, value)
        self.db.commit()

        return self.get_tournament(tournament_id)

    def delete_tournament(self, tournament_id: int, user_id: int) -> None:
        """Delete a tournament. Only allowed in DRAFT or CANCELLED."""
        tournament = self.get_tournament(tournament_id)
        self._assert_organiser(tournament, user_id)

        if tournament.status not in (TournamentStatus.DRAFT, TournamentStatus.CANCELLED):
            raise InvalidTournamentStatusError(
                tournament.status.value, "delete tournament"
            )

        self.db.delete(tournament)
        self.db.commit()
        self._log_operation("Tournament deleted", tournament_id=tournament_id)

    # Registration

    def open_registration(self, tournament_id: int, user_id: int) -> Tournament:
        """Transition DRAFT -> REGISTRATION."""
        tournament = self.get_tournament(tournament_id)
        self._assert_organiser(tournament, user_id)
        self._transition(tournament, TournamentStatus.REGISTRATION)
        return self.get_tournament(tournament_id)

    def join_tournament(
        self, tournament_id: int, team_id: int, user_id: int
    ) -> TournamentParticipant:
        """
        Captain registers their team for the tournament.

        Validations:
        - Tournament must be in REGISTRATION status
        - Team must exist and caller must be its captain
        - Team not already registered
        - Tournament not full
        """
        tournament = self.get_tournament(tournament_id)

        if tournament.status != TournamentStatus.REGISTRATION:
            raise InvalidTournamentStatusError(
                tournament.status.value, "join tournament"
            )

        # Team validation
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)
        if team.captain_id != user_id:
            raise InsufficientPermissionsError("Only the team captain can register for tournaments")

        # Duplicate check
        existing = (
            self.db.query(TournamentParticipant)
            .filter(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.team_id == team_id,
            )
            .first()
        )
        if existing:
            raise TeamAlreadyInTournamentError(team_id, tournament_id)

        # Capacity check
        current_count = (
            self.db.query(func.count(TournamentParticipant.id))
            .filter(TournamentParticipant.tournament_id == tournament_id)
            .scalar()
        )
        if current_count >= tournament.max_teams:
            raise TournamentFullError(tournament_id)

        # Assign seed based on current ELO rating (higher = better seed)
        seed = current_count + 1

        participant = TournamentParticipant(
            tournament_id=tournament_id,
            team_id=team_id,
            seed=seed,
        )
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)

        self._log_operation(
            "Team joined tournament",
            tournament_id=tournament_id,
            team_id=team_id,
            seed=seed,
        )
        return participant

    def leave_tournament(
        self, tournament_id: int, team_id: int, user_id: int
    ) -> None:
        """Captain withdraws their team. Only during REGISTRATION."""
        tournament = self.get_tournament(tournament_id)

        if tournament.status != TournamentStatus.REGISTRATION:
            raise InvalidTournamentStatusError(
                tournament.status.value, "leave tournament"
            )

        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)
        if team.captain_id != user_id:
            raise InsufficientPermissionsError("Only the team captain can withdraw")

        participant = (
            self.db.query(TournamentParticipant)
            .filter(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.team_id == team_id,
            )
            .first()
        )
        if not participant:
            raise TeamNotFoundError(f"team {team_id} in tournament {tournament_id}")

        self.db.delete(participant)
        self.db.commit()
        self._log_operation(
            "Team left tournament", tournament_id=tournament_id, team_id=team_id
        )

    # Start tournament and generate fixtures

    def start_tournament(self, tournament_id: int, user_id: int) -> Tournament:
        """
        Transition REGISTRATION -> ACTIVE and generate all fixtures.

        - Reseeds participants by ELO (descending) so top-rated teams
          get the best bracket positions / most balanced fixtures.
        - LEAGUE: generates round-robin fixtures via the circle method.
        - KNOCKOUT: generates a seeded single-elimination bracket.
        """
        tournament = self.get_tournament(tournament_id)
        self._assert_organiser(tournament, user_id)

        if tournament.status != TournamentStatus.REGISTRATION:
            raise InvalidTournamentStatusError(
                tournament.status.value, "start tournament"
            )

        participant_count = len(tournament.participants)
        if participant_count < 2:
            raise TournamentNotEnoughTeamsError(participant_count)

        # Re-seed by ELO descending (best team = seed 1)
        sorted_participants = sorted(
            tournament.participants,
            key=lambda p: (p.team.rating or 1000),
            reverse=True,
        )
        for idx, p in enumerate(sorted_participants, start=1):
            p.seed = idx
        self.db.flush()

        team_ids = [p.team_id for p in sorted_participants]

        # Generate fixtures
        if tournament.type == TournamentType.LEAGUE:
            self._generate_league_fixtures(tournament.id, team_ids)
        else:
            self._generate_knockout_fixtures(tournament.id, team_ids)

        tournament.current_round = 1
        self._transition(tournament, TournamentStatus.ACTIVE)

        # Notify all participants
        captain_ids = [p.team.captain_id for p in sorted_participants]
        self._notifier.notify_many(
            user_ids=captain_ids,
            type=NotificationType.TOURNAMENT_STARTED,
            title="Tournament Started",
            message=f"'{tournament.name}' has started! Check your fixtures.",
            related_id=tournament.id,
        )
        self.db.commit()

        self._log_operation(
            "Tournament started",
            tournament_id=tournament.id,
            type=tournament.type.value,
            teams=participant_count,
        )
        return self.get_tournament(tournament_id)

    # Match results and standings

    def record_match_result(
        self,
        tournament_id: int,
        match_id: int,
        user_id: int,
        home_score: int,
        away_score: int,
    ) -> TournamentMatch:
        """
        Record the result for a tournament match.

        Creates (or reuses) a linked Challenge in COMPLETED state,
        then recalculates standings.
        """
        tournament = self.get_tournament(tournament_id)

        if tournament.status != TournamentStatus.ACTIVE:
            raise InvalidTournamentStatusError(
                tournament.status.value, "record match result"
            )

        # Verify organiser or captain of either team
        t_match = (
            self.db.query(TournamentMatch)
            .options(
                joinedload(TournamentMatch.home_team),
                joinedload(TournamentMatch.away_team),
            )
            .filter(
                TournamentMatch.id == match_id,
                TournamentMatch.tournament_id == tournament_id,
            )
            .first()
        )
        if not t_match:
            raise TournamentNotFoundError(f"match {match_id}")

        if t_match.away_team_id is None:
            raise InvalidTournamentStatusError("BYE", "record result for a BYE match")

        # Permission: organiser or captain of either team
        is_organiser = tournament.created_by_id == user_id
        is_home_captain = t_match.home_team and t_match.home_team.captain_id == user_id
        is_away_captain = t_match.away_team and t_match.away_team.captain_id == user_id
        if not (is_organiser or is_home_captain or is_away_captain):
            raise InsufficientPermissionsError(
                "Only the organiser or a team captain can submit a result"
            )

        # Already has a completed challenge? Prevent double submission.
        if t_match.challenge_id:
            existing = self.db.query(Challenge).filter(Challenge.id == t_match.challenge_id).first()
            if existing and existing.status == ChallengeStatus.COMPLETED:
                raise InvalidTournamentStatusError("completed", "submit result again")

        # Create a Challenge record to store the actual scores
        challenge = Challenge(
            challenger_id=t_match.home_team_id,
            opponent_id=t_match.away_team_id,
            status=ChallengeStatus.COMPLETED,
            challenger_score=home_score,
            opponent_score=away_score,
            match_date=tournament.start_date,
            location=f"Tournament: {tournament.name}",
        )
        self.db.add(challenge)
        self.db.flush()

        t_match.challenge_id = challenge.id

        # Determine winner
        if home_score > away_score:
            t_match.winner_team_id = t_match.home_team_id
        elif away_score > home_score:
            t_match.winner_team_id = t_match.away_team_id
        else:
            t_match.winner_team_id = None  # draw (league only)

        # In knockout, mark loser as eliminated
        if tournament.type == TournamentType.KNOCKOUT and t_match.winner_team_id:
            loser_id = (
                t_match.away_team_id
                if t_match.winner_team_id == t_match.home_team_id
                else t_match.home_team_id
            )
            loser_participant = (
                self.db.query(TournamentParticipant)
                .filter(
                    TournamentParticipant.tournament_id == tournament_id,
                    TournamentParticipant.team_id == loser_id,
                )
                .first()
            )
            if loser_participant:
                loser_participant.is_eliminated = 1

        self.db.commit()

        # Recalculate standings
        self._recalculate_standings(tournament_id)

        # For knockout: advance winner to next round BEFORE checking completion
        # so that the final match slot exists when the completion check runs
        if tournament.type == TournamentType.KNOCKOUT:
            self.advance_knockout_winner(tournament_id, match_id)

        # Check if tournament / round is complete
        self._check_tournament_completion(tournament_id)

        self._log_operation(
            "Tournament match result recorded",
            tournament_id=tournament_id,
            match_id=match_id,
            score=f"{home_score}-{away_score}",
        )

        # Reload
        return (
            self.db.query(TournamentMatch)
            .options(
                joinedload(TournamentMatch.home_team),
                joinedload(TournamentMatch.away_team),
                joinedload(TournamentMatch.winner),
                joinedload(TournamentMatch.challenge),
            )
            .filter(TournamentMatch.id == match_id)
            .first()
        )

    def get_standings(self, tournament_id: int) -> List[TournamentParticipant]:
        """
        Return participants sorted by standings:
        1. Points (desc)
        2. Goal difference (desc)
        3. Goals scored (desc)
        """
        tournament = self.get_tournament(tournament_id)
        participants = (
            self.db.query(TournamentParticipant)
            .options(joinedload(TournamentParticipant.team))
            .filter(TournamentParticipant.tournament_id == tournament_id)
            .all()
        )
        return sorted(
            participants,
            key=lambda p: (p.points, p.goals_for - p.goals_against, p.goals_for),
            reverse=True,
        )

    def get_bracket(self, tournament_id: int) -> List[dict]:
        """
        Return knockout bracket grouped by round.

        Returns a list of dicts: [{"round_number": 1, "round_name": "...", "matches": [...]}]
        """
        tournament = self.get_tournament(tournament_id)
        matches = (
            self.db.query(TournamentMatch)
            .options(
                joinedload(TournamentMatch.home_team),
                joinedload(TournamentMatch.away_team),
                joinedload(TournamentMatch.winner),
                joinedload(TournamentMatch.challenge),
            )
            .filter(TournamentMatch.tournament_id == tournament_id)
            .order_by(TournamentMatch.round_number, TournamentMatch.match_order)
            .all()
        )

        # Group by round
        rounds: dict[int, list] = {}
        for m in matches:
            rounds.setdefault(m.round_number, []).append(m)

        total_rounds = max(rounds.keys()) if rounds else 0
        result = []
        for rnd in sorted(rounds.keys()):
            result.append({
                "round_number": rnd,
                "round_name": self._round_name(rnd, total_rounds),
                "matches": rounds[rnd],
            })
        return result

    # Cancellation

    def cancel_tournament(self, tournament_id: int, user_id: int) -> Tournament:
        """Cancel a tournament from any non-terminal state."""
        tournament = self.get_tournament(tournament_id)
        self._assert_organiser(tournament, user_id)
        self._transition(tournament, TournamentStatus.CANCELLED)
        return self.get_tournament(tournament_id)

    # Fixture generation: league (round-robin)

    def _generate_league_fixtures(
        self, tournament_id: int, team_ids: List[int]
    ) -> None:
        """
        Generate round-robin fixtures using the circle method.

        With N teams:
        - If N is odd, add a BYE placeholder (None) to make it even.
        - N-1 rounds, each with N/2 matches.
        - One team is "fixed"; others rotate clockwise each round.
        """
        teams = list(team_ids)
        has_bye = len(teams) % 2 != 0
        if has_bye:
            teams.append(None)  # BYE placeholder

        n = len(teams)
        num_rounds = n - 1
        half = n // 2

        for round_num in range(num_rounds):
            match_order = 1
            for i in range(half):
                home = teams[i]
                away = teams[n - 1 - i]

                # Skip if either side is a BYE
                if home is None or away is None:
                    continue

                t_match = TournamentMatch(
                    tournament_id=tournament_id,
                    round_number=round_num + 1,
                    match_order=match_order,
                    home_team_id=home,
                    away_team_id=away,
                )
                self.db.add(t_match)
                match_order += 1

            # Rotate: fix teams[0], rotate the rest clockwise
            teams = [teams[0]] + [teams[-1]] + teams[1:-1]

        self.db.flush()
        self._log_operation(
            "League fixtures generated",
            tournament_id=tournament_id,
            rounds=num_rounds,
        )

    # Fixture generation: knockout (single elimination)

    def _generate_knockout_fixtures(
        self, tournament_id: int, team_ids: List[int]
    ) -> None:
        """
        Generate a seeded single-elimination bracket.

        - Pad to next power of 2 with BYEs.
        - Seed placement: 1 vs N, 2 vs N-1, etc.
        - BYE matches auto-advance the non-BYE team.
        - Subsequent rounds have empty match slots that fill as winners advance.
        """
        n = len(team_ids)
        bracket_size = 1
        while bracket_size < n:
            bracket_size *= 2

        total_rounds = int(math.log2(bracket_size))

        # Pad with None (BYE)
        seeded = list(team_ids) + [None] * (bracket_size - n)

        # Create seeded pairings for round 1
        # Standard bracket: seed 1 vs last, seed 2 vs second-last, etc.
        round1_pairs = []
        for i in range(bracket_size // 2):
            round1_pairs.append((seeded[i], seeded[bracket_size - 1 - i]))

        # Round 1 matches
        match_order = 1
        round1_matches = []
        for home_id, away_id in round1_pairs:
            t_match = TournamentMatch(
                tournament_id=tournament_id,
                round_number=1,
                match_order=match_order,
                home_team_id=home_id if home_id else away_id,  # ensure home is non-None
                away_team_id=away_id if home_id else None,
            )
            self.db.add(t_match)
            self.db.flush()
            round1_matches.append(t_match)

            # Auto-advance BYE matches
            if home_id is None or away_id is None:
                winner_id = home_id or away_id
                t_match.winner_team_id = winner_id
                # Mark as completed BYE — no challenge needed

            match_order += 1

        # Create placeholder matches for subsequent rounds (only when BYE winners are known)
        prev_round_matches = round1_matches
        for rnd in range(2, total_rounds + 1):
            current_round_matches = []
            num_matches = len(prev_round_matches) // 2
            for i in range(num_matches):
                m1 = prev_round_matches[2 * i]
                m2 = prev_round_matches[2 * i + 1]

                home = m1.winner_team_id if m1 else None
                away = m2.winner_team_id if m2 else None

                if not home and not away:
                    # Both TBD — skip; advance_knockout_winner will create this match
                    current_round_matches.append(None)
                    continue

                t_match = TournamentMatch(
                    tournament_id=tournament_id,
                    round_number=rnd,
                    match_order=i + 1,
                    home_team_id=home or away,
                    away_team_id=away if home else None,
                )
                self.db.add(t_match)
                self.db.flush()

                # Auto-advance if only one team
                if home and not away:
                    t_match.winner_team_id = home
                elif away and not home:
                    t_match.winner_team_id = away

                current_round_matches.append(t_match)

            prev_round_matches = current_round_matches

        self.db.flush()
        self._log_operation(
            "Knockout bracket generated",
            tournament_id=tournament_id,
            bracket_size=bracket_size,
            total_rounds=total_rounds,
        )

    def advance_knockout_winner(
        self, tournament_id: int, match_id: int
    ) -> None:
        """
        After a knockout match result is recorded, propagate the winner
        into the next round's bracket slot.
        """
        t_match = (
            self.db.query(TournamentMatch)
            .filter(
                TournamentMatch.id == match_id,
                TournamentMatch.tournament_id == tournament_id,
            )
            .first()
        )
        if not t_match or not t_match.winner_team_id:
            return

        # Find the next round match this winner feeds into
        next_round = t_match.round_number + 1
        # Match order in next round: ceil(current_match_order / 2)
        next_match_order = math.ceil(t_match.match_order / 2)

        next_match = (
            self.db.query(TournamentMatch)
            .filter(
                TournamentMatch.tournament_id == tournament_id,
                TournamentMatch.round_number == next_round,
                TournamentMatch.match_order == next_match_order,
            )
            .first()
        )
        if not next_match:
            # Check if a next round is expected (not the final)
            round1_count = (
                self.db.query(TournamentMatch)
                .filter(
                    TournamentMatch.tournament_id == tournament_id,
                    TournamentMatch.round_number == 1,
                )
                .count()
            )
            total_rounds = round1_count.bit_length() if round1_count else 0
            if t_match.round_number >= total_rounds:
                self.db.commit()
                return  # This was the final

            # Create the next-round match with this winner as the first known team
            next_match = TournamentMatch(
                tournament_id=tournament_id,
                round_number=next_round,
                match_order=next_match_order,
                home_team_id=t_match.winner_team_id,
                away_team_id=None,
            )
            self.db.add(next_match)
            self.db.flush()
            self.db.commit()
            return

        # Odd match_order → fills home_team; even → fills away_team
        if t_match.match_order % 2 == 1:
            next_match.home_team_id = t_match.winner_team_id
        else:
            next_match.away_team_id = t_match.winner_team_id

        self.db.commit()

    # Standings recalculation

    def _recalculate_standings(self, tournament_id: int) -> None:
        """
        Recalculate denormalised standings for all participants
        from completed tournament matches.

        Points: 3 for win, 1 for draw, 0 for loss.
        """
        participants = (
            self.db.query(TournamentParticipant)
            .filter(TournamentParticipant.tournament_id == tournament_id)
            .all()
        )

        # Build a map: team_id -> participant
        pmap = {p.team_id: p for p in participants}

        # Reset all
        for p in participants:
            p.played = 0
            p.wins = 0
            p.draws = 0
            p.losses = 0
            p.goals_for = 0
            p.goals_against = 0
            p.points = 0

        # Scan completed matches
        matches = (
            self.db.query(TournamentMatch)
            .join(Challenge, TournamentMatch.challenge_id == Challenge.id)
            .filter(
                TournamentMatch.tournament_id == tournament_id,
                Challenge.status == ChallengeStatus.COMPLETED,
            )
            .all()
        )

        for m in matches:
            challenge = self.db.query(Challenge).filter(Challenge.id == m.challenge_id).first()
            if not challenge:
                continue

            home_id = m.home_team_id
            away_id = m.away_team_id
            if not away_id:
                continue  # BYE

            h_score = challenge.challenger_score or 0
            a_score = challenge.opponent_score or 0

            home_p = pmap.get(home_id)
            away_p = pmap.get(away_id)
            if not home_p or not away_p:
                continue

            home_p.played += 1
            away_p.played += 1
            home_p.goals_for += h_score
            home_p.goals_against += a_score
            away_p.goals_for += a_score
            away_p.goals_against += h_score

            if h_score > a_score:
                home_p.wins += 1
                home_p.points += 3
                away_p.losses += 1
            elif a_score > h_score:
                away_p.wins += 1
                away_p.points += 3
                home_p.losses += 1
            else:
                home_p.draws += 1
                away_p.draws += 1
                home_p.points += 1
                away_p.points += 1

        self.db.commit()
        self._log_operation("Standings recalculated", tournament_id=tournament_id)

    # Completion check

    def _check_tournament_completion(self, tournament_id: int) -> None:
        """
        Check if all matches in the tournament are done.
        If so, transition to COMPLETED and notify participants.
        """
        tournament = self.get_tournament(tournament_id)
        if tournament.status != TournamentStatus.ACTIVE:
            return

        total_matches = (
            self.db.query(func.count(TournamentMatch.id))
            .filter(
                TournamentMatch.tournament_id == tournament_id,
                TournamentMatch.away_team_id.isnot(None),  # exclude BYEs
            )
            .scalar()
        )
        completed_matches = (
            self.db.query(func.count(TournamentMatch.id))
            .filter(
                TournamentMatch.tournament_id == tournament_id,
                TournamentMatch.challenge_id.isnot(None),
                TournamentMatch.away_team_id.isnot(None),
            )
            .scalar()
        )

        if completed_matches >= total_matches and total_matches > 0:
            self._transition(tournament, TournamentStatus.COMPLETED)

            # Notify all participants
            participants = (
                self.db.query(TournamentParticipant)
                .options(joinedload(TournamentParticipant.team))
                .filter(TournamentParticipant.tournament_id == tournament_id)
                .all()
            )
            captain_ids = [p.team.captain_id for p in participants]
            self._notifier.notify_many(
                user_ids=captain_ids,
                type=NotificationType.TOURNAMENT_COMPLETED,
                title="Tournament Completed",
                message=f"'{tournament.name}' has finished! Check the final standings.",
                related_id=tournament.id,
            )
            self.db.commit()

            self._log_operation(
                "Tournament auto-completed", tournament_id=tournament_id
            )

    # Internal helpers

    def _transition(self, tournament: Tournament, target: TournamentStatus) -> None:
        """Validate and execute a status transition."""
        allowed = _VALID_TRANSITIONS.get(tournament.status, set())
        if target not in allowed:
            raise InvalidTournamentStatusError(
                tournament.status.value, f"transition to {target.value}"
            )
        tournament.status = target
        self.db.commit()
        self._log_operation(
            "Tournament state transition",
            tournament_id=tournament.id,
            transition=f"{tournament.status.value} -> {target.value}",
        )

    def _assert_organiser(self, tournament: Tournament, user_id: int) -> None:
        """Verify that user_id is the tournament organiser."""
        if tournament.created_by_id != user_id:
            raise InsufficientPermissionsError(
                "Only the tournament organiser can perform this action"
            )

    @staticmethod
    def _round_name(round_number: int, total_rounds: int) -> str:
        """Human-readable round name for knockout brackets."""
        remaining = total_rounds - round_number
        if remaining == 0:
            return "Final"
        if remaining == 1:
            return "Semi-finals"
        if remaining == 2:
            return "Quarter-finals"
        if remaining == 3:
            return "Round of 16"
        return f"Round {round_number}"
