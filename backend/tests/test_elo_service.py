"""
test_elo_service.py — Unit tests for EloService
=================================================

Two categories of tests are present:

1. Pure mathematical tests (no database required)
   These test the static helper methods that implement the core ELO
   formulas.  They call the methods directly without instantiating a
   service or touching the database.

2. Integration tests (database required)
   These test update_ratings(), which reads a completed Challenge,
   computes the new ratings, persists Rating audit records, and
   updates the Team rows in one transaction.

ELO formulas under test:
    E_A = 1 / (1 + 10^((R_B - R_A) / 400))      expected score
    S_A = 1.0 (win) | 0.5 (draw) | 0.0 (loss)   actual score
    R'_A = R_A + K * (S_A - E_A)                 new rating
    G    = 1 + ln(1 + |goal_diff|)               goal-diff multiplier
"""

import math
import pytest
from sqlalchemy.orm import Session

from app.services.elo_service import EloService
from app.models.challenge import Challenge, ChallengeStatus
from app.models.rating import Rating
from app.models.team import Team
from app.models.user import User


# TC-E01  Expected score formula

class TestExpectedScore:

    def test_equal_ratings_give_half(self):
        """
        TC-E01-A: Two teams with identical ratings each have a 50 % chance.

        With R_A = R_B = 1000:
            E_A = 1 / (1 + 10^0) = 1 / 2 = 0.5
        """
        result = EloService._expected_score(1000, 1000)
        assert result == pytest.approx(0.5, abs=1e-6)

    def test_higher_rating_gives_above_half(self):
        """
        TC-E01-B: A team with a higher rating has a probability > 0.5.

        The stronger team is expected to win more often than the weaker.
        """
        result = EloService._expected_score(1200, 1000)  # A is stronger
        assert result > 0.5

    def test_lower_rating_gives_below_half(self):
        """
        TC-E01-C: A team with a lower rating has a probability < 0.5.
        """
        result = EloService._expected_score(800, 1000)  # A is weaker
        assert result < 0.5

    def test_expected_scores_sum_to_one(self):
        """
        TC-E01-D: E_A + E_B always sums to exactly 1.0.

        This is a fundamental invariant of the ELO system.
        """
        r_a, r_b = 1150, 950
        e_a = EloService._expected_score(r_a, r_b)
        e_b = EloService._expected_score(r_b, r_a)
        assert e_a + e_b == pytest.approx(1.0, abs=1e-9)

    def test_400_point_gap_gives_ten_to_one_odds(self):
        """
        TC-E01-E: A 400-point rating gap gives approximately 10:1 odds.

        By definition of the ELO formula with divisor 400:
            E_A = 1 / (1 + 10^1) ≈ 0.0909
            E_B = 1 / (1 + 10^-1) ≈ 0.9091
        """
        e_weaker  = EloService._expected_score(1000, 1400)
        e_stronger = EloService._expected_score(1400, 1000)
        assert e_weaker   == pytest.approx(1 / 11, abs=1e-4)
        assert e_stronger == pytest.approx(10 / 11, abs=1e-4)


# TC-E02  Actual score mapping

class TestActualScores:

    def test_win_returns_one_zero(self):
        """
        TC-E02-A: Challenger win → S_A=1.0, S_B=0.0
        """
        s_a, s_b = EloService._actual_scores(3, 1)
        assert s_a == 1.0
        assert s_b == 0.0

    def test_draw_returns_half_half(self):
        """
        TC-E02-B: Draw → S_A=0.5, S_B=0.5
        """
        s_a, s_b = EloService._actual_scores(2, 2)
        assert s_a == 0.5
        assert s_b == 0.5

    def test_loss_returns_zero_one(self):
        """
        TC-E02-C: Challenger loss → S_A=0.0, S_B=1.0
        """
        s_a, s_b = EloService._actual_scores(0, 2)
        assert s_a == 0.0
        assert s_b == 1.0

    @pytest.mark.parametrize("score_a,score_b,expected_a", [
        (5, 0, 1.0),
        (0, 5, 0.0),
        (1, 1, 0.5),
        (0, 0, 0.5),
    ])
    def test_actual_scores_parametrized(self, score_a, score_b, expected_a):
        """
        TC-E02-D: Parametrized sweep over typical match scorelines.
        """
        s_a, _ = EloService._actual_scores(score_a, score_b)
        assert s_a == expected_a


# TC-E03  Goal-difference multiplier

class TestGoalDifferenceMultiplier:

    def test_zero_goal_diff_gives_base_multiplier(self):
        """
        TC-E03-A: A draw (0 goals difference) gives G = 1 + ln(1) = 1.0.
        """
        result = EloService._goal_difference_multiplier(0)
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_one_goal_diff_amplifies_k(self):
        """
        TC-E03-B: A 1-goal margin gives G = 1 + ln(2) ≈ 1.693.
        """
        result = EloService._goal_difference_multiplier(1)
        assert result == pytest.approx(1.0 + math.log(2), abs=1e-6)

    def test_multiplier_increases_with_goal_diff(self):
        """
        TC-E03-C: Larger goal margins produce larger multipliers.

        This rewards dominant victories with bigger rating swings.
        """
        g1 = EloService._goal_difference_multiplier(1)
        g3 = EloService._goal_difference_multiplier(3)
        g5 = EloService._goal_difference_multiplier(5)
        assert g1 < g3 < g5

    def test_multiplier_always_at_least_one(self):
        """
        TC-E03-D: The multiplier is always ≥ 1 (never reduces K-factor).
        """
        for diff in range(10):
            assert EloService._goal_difference_multiplier(diff) >= 1.0


# TC-E04  Dynamic K-factor selection

class TestDynamicKFactor:
    """
    K-factor tiers (from elo_service.py):
        < 10 matches  → K_base = 40  (provisional)
        10–29 matches → K_base = 30  (developing)
        ≥ 30 matches  → K_base = 20  (established)

    Effective K = K_base * G(|goal_diff|)
    """

    def _svc(self, db):
        return EloService(db)

    def test_k_factor_provisional_team(self, db: Session):
        """
        TC-E04-A: A new team (< 10 matches) receives K_base = 40.

        With a 1-goal margin (G ≈ 1.693), K_eff = 40 * 1.693 ≈ 67.7.
        """
        svc = self._svc(db)
        k = svc._dynamic_k_factor(matches_played=5, goal_diff=1)
        expected_k_base = 40
        expected_g      = EloService._goal_difference_multiplier(1)
        assert k == pytest.approx(expected_k_base * expected_g, abs=1e-6)

    def test_k_factor_developing_team(self, db: Session):
        """
        TC-E04-B: A developing team (10–29 matches) receives K_base = 30.
        """
        svc = self._svc(db)
        k = svc._dynamic_k_factor(matches_played=15, goal_diff=0)
        expected_k_base = 30
        expected_g      = EloService._goal_difference_multiplier(0)
        assert k == pytest.approx(expected_k_base * expected_g, abs=1e-6)

    def test_k_factor_established_team(self, db: Session):
        """
        TC-E04-C: An established team (≥ 30 matches) receives K_base = 20.
        """
        svc = self._svc(db)
        k = svc._dynamic_k_factor(matches_played=50, goal_diff=2)
        expected_k_base = 20
        expected_g      = EloService._goal_difference_multiplier(2)
        assert k == pytest.approx(expected_k_base * expected_g, abs=1e-6)

    def test_k_factor_at_tier_boundaries(self, db: Session):
        """
        TC-E04-D: Verify exact tier boundary behaviour (9 vs 10, 29 vs 30).
        """
        svc = self._svc(db)
        k_at_9  = svc._dynamic_k_factor(9,  goal_diff=0)   # still provisional
        k_at_10 = svc._dynamic_k_factor(10, goal_diff=0)   # now developing
        k_at_29 = svc._dynamic_k_factor(29, goal_diff=0)   # still developing
        k_at_30 = svc._dynamic_k_factor(30, goal_diff=0)   # now established

        assert k_at_9  > k_at_10   # 40 > 30
        assert k_at_29 > k_at_30   # 30 > 20


# TC-E05  Full ELO update via database

class TestUpdateRatings:

    def test_winner_gains_loser_loses(
        self,
        db: Session,
        accepted_challenge: Challenge,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-E05-A: After a win, the winner's rating increases and the
        loser's rating decreases.

        Both teams start at 1000.  Team Alpha wins 3-1.
        The sum of both new ratings must equal the sum of old ratings
        (ELO is zero-sum).
        """
        # Mark challenge COMPLETED with scores
        accepted_challenge.status           = ChallengeStatus.COMPLETED
        accepted_challenge.challenger_score = 3
        accepted_challenge.opponent_score   = 1
        db.commit()

        svc = EloService(db)
        update_a, update_b = svc.update_ratings(accepted_challenge.id)

        # Winner gains, loser loses
        assert update_a.rating_change > 0, "Challenger (winner) must gain rating"
        assert update_b.rating_change < 0, "Opponent  (loser)  must lose rating"

        # Zero-sum property: points gained == points lost
        assert update_a.rating_change + update_b.rating_change == 0

    def test_draw_changes_are_symmetric_for_equal_teams(
        self,
        db: Session,
        accepted_challenge: Challenge,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-E05-B: A draw between equally-rated teams produces minimal,
        symmetric rating changes.

        When E_A == E_B == 0.5 and S_A == S_B == 0.5, the delta is 0
        for both teams.  Allowing for rounding: |Δ| ≤ 1.
        """
        accepted_challenge.status           = ChallengeStatus.COMPLETED
        accepted_challenge.challenger_score = 1
        accepted_challenge.opponent_score   = 1
        db.commit()

        svc = EloService(db)
        update_a, update_b = svc.update_ratings(accepted_challenge.id)

        assert abs(update_a.rating_change) <= 1
        assert abs(update_b.rating_change) <= 1

    def test_underdog_win_yields_larger_gain(
        self,
        db: Session,
        captain_a: User,
        captain_b: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-E05-C: An underdog beating a stronger opponent gains more points
        than the same win between equal teams.

        Team Alpha (R=800) beats Team Beta (R=1200).
        Team Alpha's gain must be larger than it would be between equal teams.
        """
        # Make team_a the underdog
        team_a.rating = 800
        team_b.rating = 1200
        db.commit()

        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.COMPLETED,
            challenger_score=2,
            opponent_score=1,
        )
        db.add(challenge)
        db.commit()

        svc = EloService(db)
        update_a, update_b = svc.update_ratings(challenge.id)

        # Underdog gain must exceed the 50 % K-factor (K*0.5 for equal teams)
        # With K=40 (provisional) and G≈1.693 the gain must be substantial.
        assert update_a.rating_change > 0
        assert update_a.rating_change > 20  # clearly > equal-team baseline

    def test_update_ratings_persists_rating_audit_records(
        self,
        db: Session,
        accepted_challenge: Challenge,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-E05-D: update_ratings() creates exactly two Rating audit rows —
        one for each participating team.

        These immutable records form the historical ELO log described in
        the data model (section 3.3.3).
        """
        accepted_challenge.status           = ChallengeStatus.COMPLETED
        accepted_challenge.challenger_score = 2
        accepted_challenge.opponent_score   = 0
        db.commit()

        svc = EloService(db)
        svc.update_ratings(accepted_challenge.id)

        records = (
            db.query(Rating)
            .filter(Rating.challenge_id == accepted_challenge.id)
            .all()
        )
        assert len(records) == 2  # one record per team

        team_ids = {r.team_id for r in records}
        assert team_a.id in team_ids
        assert team_b.id in team_ids

    def test_update_ratings_updates_team_rating_column(
        self,
        db: Session,
        accepted_challenge: Challenge,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-E05-E: After update_ratings(), the rating column on the Team
        model is updated to the new value.

        Verifies that the service writes back to the team row, not just
        the audit log.
        """
        initial_rating_a = team_a.rating  # 1000
        initial_rating_b = team_b.rating  # 1000

        accepted_challenge.status           = ChallengeStatus.COMPLETED
        accepted_challenge.challenger_score = 3
        accepted_challenge.opponent_score   = 0
        db.commit()

        svc = EloService(db)
        svc.update_ratings(accepted_challenge.id)

        db.refresh(team_a)
        db.refresh(team_b)

        assert team_a.rating != initial_rating_a  # changed
        assert team_b.rating != initial_rating_b  # changed

    def test_update_ratings_raises_for_pending_challenge(
        self,
        db: Session,
        captain_a: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-E05-F: Calling update_ratings() on a non-COMPLETED challenge
        raises a ValueError.

        Verifies the guard that prevents ELO calculation without a
        confirmed match result.
        """
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.PENDING,
        )
        db.add(challenge)
        db.commit()

        svc = EloService(db)
        # The error message reports the *current* state of the challenge,
        # i.e. "...in state 'pending'", not the required state "COMPLETED".
        with pytest.raises(ValueError, match="pending"):
            svc.update_ratings(challenge.id)
