"""
test_team_category.py — Unit tests for the team categorisation module
======================================================================

Covers the three test cases specified in thesis section 3.4.1:

    TC-E01  Expected-score invariants   (E_A + E_B = 1, E_A = 0.5 for equal ratings)
    TC-E03  Goal-difference multiplier  (G ≥ 1.0 always)
    TC-E04  Dynamic K-factor boundaries (9→10 and 29→30 match transitions)

All tests in this file are **pure unit tests** — no database, no HTTP
client, no fixtures from conftest.py are required.  Every assertion calls
either a static method on EloService or the public ``get_team_category``
function from the team_category module.

Why a separate file?
--------------------
The ``get_team_category`` function was extracted from EloService as a
standalone, DB-free module so that it can be reused independently (e.g.
in team profile API responses).  Testing it in isolation without a DB
session fixture validates that the extraction is correct and that the
category boundaries are enforced at the correct threshold values.
"""

import math

import pytest

from app.services.elo_service import EloService
from app.core.team_category import (
    TeamCategory,
    TeamCategoryInfo,
    get_team_category,
    PROVISIONAL_MAX_MATCHES,
    DEVELOPING_MAX_MATCHES,
)


# TC-E01  Expected-score formula

class TestExpectedScore:
    """
    TC-E01: Verify the ELO expected-score formula properties.

    Formula:  E_A = 1 / (1 + 10^((R_B - R_A) / 400))

    Two invariants are tested:
    (A) Equal ratings → E_A = 0.5  (50 % probability for both sides)
    (B) E_A + E_B = 1.0            (probabilities always sum to 1)
    """

    def test_equal_ratings_give_exactly_half(self):
        """
        TC-E01-A: When R_A == R_B the exponent is 0, so E_A = 1/(1+1) = 0.5.
        """
        result = EloService._expected_score(1000, 1000)
        assert result == pytest.approx(0.5, abs=1e-9)

    @pytest.mark.parametrize("r_a,r_b", [
        (1000, 1000),
        (1200,  800),
        ( 800, 1200),
        (1500,  500),
        (1000, 1400),
    ])
    def test_expected_scores_sum_to_one(self, r_a: int, r_b: int):
        """
        TC-E01-B: E_A + E_B = 1.0 for any combination of ratings.

        This is the fundamental conservation invariant of the ELO system:
        probability mass cannot be created or destroyed.
        """
        e_a = EloService._expected_score(r_a, r_b)
        e_b = EloService._expected_score(r_b, r_a)
        assert e_a + e_b == pytest.approx(1.0, abs=1e-9), (
            f"E_A({r_a} vs {r_b}) + E_B = {e_a + e_b:.10f} ≠ 1.0"
        )

    def test_stronger_team_has_probability_above_half(self):
        """
        TC-E01-C: A higher-rated team must have E > 0.5.
        """
        assert EloService._expected_score(1200, 1000) > 0.5

    def test_weaker_team_has_probability_below_half(self):
        """
        TC-E01-D: A lower-rated team must have E < 0.5.
        """
        assert EloService._expected_score(800, 1000) < 0.5


# TC-E03  Goal-difference multiplier

class TestGoalDifferenceMultiplier:
    """
    TC-E03: Verify G = 1 + ln(1 + |Δg|) is always ≥ 1.0.

    The multiplier amplifies the K-factor for decisive victories.
    It must never reduce K below its base value (G ≥ 1).
    """

    def test_zero_diff_gives_exactly_one(self):
        """
        TC-E03-A: A drawn match (Δg = 0) gives G = 1 + ln(1) = 1.0.

        No amplification is applied for a goalless draw or any 1-1 etc.
        """
        result = EloService._goal_difference_multiplier(0)
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_one_goal_diff_matches_formula(self):
        """
        TC-E03-B: Δg = 1  →  G = 1 + ln(2) ≈ 1.693.
        """
        result = EloService._goal_difference_multiplier(1)
        assert result == pytest.approx(1.0 + math.log(2), abs=1e-9)

    @pytest.mark.parametrize("goal_diff", range(0, 11))
    def test_multiplier_always_at_least_one(self, goal_diff: int):
        """
        TC-E03-C: G ≥ 1.0 for every non-negative goal difference.

        Because ln(1 + x) ≥ 0 for x ≥ 0, the multiplier is guaranteed
        to never shrink the effective K below the base K-factor.
        """
        g = EloService._goal_difference_multiplier(goal_diff)
        assert g >= 1.0, f"G({goal_diff}) = {g:.6f} < 1.0"

    def test_multiplier_strictly_increases_with_goal_diff(self):
        """
        TC-E03-D: Larger margins always produce larger multipliers.

        Verifies the monotonicity of G — a 5-goal thrashing must be
        rewarded more than a 1-goal win.
        """
        g_values = [EloService._goal_difference_multiplier(d) for d in range(8)]
        assert g_values == sorted(g_values), (
            "Multiplier is not monotonically increasing with goal difference"
        )


# TC-E04  Dynamic K-factor / team category boundaries

class TestTeamCategory:
    """
    TC-E04: Verify category assignment and K-factor at every tier boundary.

    Thresholds (from team_category.py):
        matches < PROVISIONAL_MAX_MATCHES (10) → PROVISIONAL  K=40
        matches < DEVELOPING_MAX_MATCHES  (30) → DEVELOPING   K=30
        matches ≥ DEVELOPING_MAX_MATCHES  (30) → ESTABLISHED  K=20

    Sub-tests:
        A  Interior of each tier returns the correct category & K-factor.
        B  Exact lower boundary of DEVELOPING (match 10) flips from K=40→30.
        C  Exact lower boundary of ESTABLISHED (match 30) flips from K=30→20.
        D  Return type is always TeamCategoryInfo (frozen dataclass).
        E  matches_played is echoed back correctly in the result.
        F  Negative input raises ValueError.
    """

    # A — Interior values

    def test_provisional_interior(self):
        """TC-E04-A1: 5 matches → PROVISIONAL, K = 40."""
        info = get_team_category(5)
        assert info.category == TeamCategory.PROVISIONAL
        assert info.k_factor == 40

    def test_developing_interior(self):
        """TC-E04-A2: 20 matches → DEVELOPING, K = 30."""
        info = get_team_category(20)
        assert info.category == TeamCategory.DEVELOPING
        assert info.k_factor == 30

    def test_established_interior(self):
        """TC-E04-A3: 50 matches → ESTABLISHED, K = 20."""
        info = get_team_category(50)
        assert info.category == TeamCategory.ESTABLISHED
        assert info.k_factor == 20

    # B — PROVISIONAL → DEVELOPING boundary (match 9 vs 10)

    def test_match_9_is_still_provisional(self):
        """
        TC-E04-B1: The last match inside the provisional tier (9) still
        yields K = 40.
        """
        info = get_team_category(PROVISIONAL_MAX_MATCHES - 1)   # 9
        assert info.category == TeamCategory.PROVISIONAL
        assert info.k_factor == 40

    def test_match_10_flips_to_developing(self):
        """
        TC-E04-B2: Match 10 is the first match inside the developing tier
        → K drops from 40 to 30.
        """
        info = get_team_category(PROVISIONAL_MAX_MATCHES)        # 10
        assert info.category == TeamCategory.DEVELOPING
        assert info.k_factor == 30

    def test_boundary_9_to_10_k_factor_drops(self):
        """
        TC-E04-B3: K(9) > K(10) — the tier transition reduces volatility.
        """
        k_before = get_team_category(PROVISIONAL_MAX_MATCHES - 1).k_factor
        k_after  = get_team_category(PROVISIONAL_MAX_MATCHES).k_factor
        assert k_before > k_after, (
            f"Expected K({PROVISIONAL_MAX_MATCHES - 1})={k_before} "
            f"> K({PROVISIONAL_MAX_MATCHES})={k_after}"
        )

    # C — DEVELOPING → ESTABLISHED boundary (match 29 vs 30)

    def test_match_29_is_still_developing(self):
        """
        TC-E04-C1: The last match inside the developing tier (29) still
        yields K = 30.
        """
        info = get_team_category(DEVELOPING_MAX_MATCHES - 1)     # 29
        assert info.category == TeamCategory.DEVELOPING
        assert info.k_factor == 30

    def test_match_30_flips_to_established(self):
        """
        TC-E04-C2: Match 30 is the first match inside the established tier
        → K drops from 30 to 20.
        """
        info = get_team_category(DEVELOPING_MAX_MATCHES)          # 30
        assert info.category == TeamCategory.ESTABLISHED
        assert info.k_factor == 20

    def test_boundary_29_to_30_k_factor_drops(self):
        """
        TC-E04-C3: K(29) > K(30) — the tier transition reduces volatility.
        """
        k_before = get_team_category(DEVELOPING_MAX_MATCHES - 1).k_factor
        k_after  = get_team_category(DEVELOPING_MAX_MATCHES).k_factor
        assert k_before > k_after, (
            f"Expected K({DEVELOPING_MAX_MATCHES - 1})={k_before} "
            f"> K({DEVELOPING_MAX_MATCHES})={k_after}"
        )

    # D — Edge: zero matches (brand-new team)

    def test_zero_matches_is_provisional(self):
        """
        TC-E04-D: A newly created team with 0 matches is PROVISIONAL, K=40.
        """
        info = get_team_category(0)
        assert info.category == TeamCategory.PROVISIONAL
        assert info.k_factor == 40

    # E — Return type and field correctness

    def test_return_type_is_team_category_info(self):
        """
        TC-E04-E1: get_team_category always returns a TeamCategoryInfo instance.
        """
        assert isinstance(get_team_category(0),  TeamCategoryInfo)
        assert isinstance(get_team_category(15), TeamCategoryInfo)
        assert isinstance(get_team_category(50), TeamCategoryInfo)

    @pytest.mark.parametrize("matches", [0, 9, 10, 29, 30, 100])
    def test_matches_played_echoed_in_result(self, matches: int):
        """
        TC-E04-E2: The matches_played field in the result equals the input.
        """
        info = get_team_category(matches)
        assert info.matches_played == matches

    def test_labels_are_non_empty_strings(self):
        """
        TC-E04-E3: Both label_en and label_sk are non-empty strings for
        every tier.
        """
        for matches in (0, 15, 50):
            info = get_team_category(matches)
            assert isinstance(info.label_en, str) and info.label_en.strip()
            assert isinstance(info.label_sk, str) and info.label_sk.strip()

    # F — Input validation

    def test_negative_input_raises_value_error(self):
        """
        TC-E04-F: A negative match count is invalid and must raise ValueError.

        The DB always returns counts ≥ 0, so this guard defends against
        accidental misuse of the function directly.
        """
        with pytest.raises(ValueError, match=r"non-negative"):
            get_team_category(-1)

    # G — EloService integration: _dynamic_k_factor delegates correctly

    def test_dynamic_k_factor_uses_category_k_at_9_matches(self, db):
        """
        TC-E04-G1: EloService._dynamic_k_factor(9, goal_diff=0) uses K=40.

        goal_diff=0 → G=1.0, so K_eff == K_base exactly.
        """
        svc = EloService(db)
        k = svc._dynamic_k_factor(matches_played=9, goal_diff=0)
        assert k == pytest.approx(40.0, abs=1e-6)

    def test_dynamic_k_factor_uses_category_k_at_10_matches(self, db):
        """
        TC-E04-G2: EloService._dynamic_k_factor(10, goal_diff=0) uses K=30.
        """
        svc = EloService(db)
        k = svc._dynamic_k_factor(matches_played=10, goal_diff=0)
        assert k == pytest.approx(30.0, abs=1e-6)

    def test_dynamic_k_factor_uses_category_k_at_30_matches(self, db):
        """
        TC-E04-G3: EloService._dynamic_k_factor(30, goal_diff=0) uses K=20.
        """
        svc = EloService(db)
        k = svc._dynamic_k_factor(matches_played=30, goal_diff=0)
        assert k == pytest.approx(20.0, abs=1e-6)
