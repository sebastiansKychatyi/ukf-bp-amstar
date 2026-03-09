"""
test_pydantic_schemas.py — Pydantic V2 schema validation tests
==============================================================

These tests verify that the request/response schemas enforce their
declared field constraints *before* any business logic or database
interaction takes place.  A ValidationError raised at the schema
boundary prevents invalid data from reaching the service layer.

Test categories:
    TC-P01  ChallengeCreate — input validation
    TC-P02  ChallengeResultSubmit — score field constraints
    TC-P03  ChallengeStatus — enum normalisation
    TC-P04  ChallengeResponse — ORM serialisation via model_validate
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.challenge import (
    ChallengeCreate,
    ChallengeResultSubmit,
    ChallengeResponse,
    TeamBrief,
)
from app.models.challenge import ChallengeStatus


# =============================================================================
# TC-P01  ChallengeCreate — input validation
# =============================================================================

class TestChallengeCreate:

    def test_valid_minimal_payload(self):
        """
        TC-P01-A: Only opponent_id is required; all other fields are optional.

        Verifies that a minimal payload with a valid opponent_id passes
        validation and that optional fields default to None.
        """
        data = ChallengeCreate(opponent_id=5)

        assert data.opponent_id == 5
        assert data.match_date is None
        assert data.location is None
        assert data.message is None

    def test_valid_full_payload(self):
        """
        TC-P01-B: A fully populated payload with all optional fields passes.
        """
        data = ChallengeCreate(
            opponent_id=7,
            match_date=datetime(2026, 6, 15, 18, 0, 0, tzinfo=timezone.utc),
            location="Štadión Nitra",
            message="Calling you out!",
        )

        assert data.opponent_id == 7
        assert data.location == "Štadión Nitra"

    def test_opponent_id_zero_raises(self):
        """
        TC-P01-C: opponent_id=0 violates the gt=0 constraint.

        The field declares Field(..., gt=0), so zero is invalid.
        """
        with pytest.raises(ValidationError) as exc_info:
            ChallengeCreate(opponent_id=0)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("opponent_id",) for e in errors)

    def test_opponent_id_negative_raises(self):
        """
        TC-P01-D: Negative opponent_id violates the gt=0 constraint.
        """
        with pytest.raises(ValidationError) as exc_info:
            ChallengeCreate(opponent_id=-1)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("opponent_id",) for e in errors)

    def test_location_too_long_raises(self):
        """
        TC-P01-E: A location string exceeding 200 characters is rejected.

        The field declares max_length=200.
        """
        with pytest.raises(ValidationError) as exc_info:
            ChallengeCreate(opponent_id=1, location="A" * 201)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("location",) for e in errors)

    def test_location_at_max_length_passes(self):
        """
        TC-P01-F: A location string of exactly 200 characters is accepted.

        Verifies the boundary condition: max_length is inclusive.
        """
        data = ChallengeCreate(opponent_id=1, location="A" * 200)
        assert len(data.location) == 200

    def test_message_too_long_raises(self):
        """
        TC-P01-G: A message exceeding 500 characters is rejected.
        """
        with pytest.raises(ValidationError):
            ChallengeCreate(opponent_id=1, message="B" * 501)

    def test_missing_opponent_id_raises(self):
        """
        TC-P01-H: Omitting the required opponent_id field raises ValidationError.
        """
        with pytest.raises(ValidationError) as exc_info:
            ChallengeCreate()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("opponent_id",) for e in errors)

    def test_string_opponent_id_coerced_to_int(self):
        """
        TC-P01-I: Pydantic V2 coerces a numeric string to int in lax mode.

        The HTTP layer passes JSON, so "5" from a query param may arrive
        as str; Pydantic should coerce it silently.
        """
        data = ChallengeCreate(opponent_id="5")  # type: ignore[arg-type]
        assert data.opponent_id == 5


# =============================================================================
# TC-P02  ChallengeResultSubmit — score field constraints
# =============================================================================

class TestChallengeResultSubmit:

    def test_valid_scores(self):
        """
        TC-P02-A: Typical match scores (0–99) pass all constraints.
        """
        data = ChallengeResultSubmit(challenger_score=3, opponent_score=1)

        assert data.challenger_score == 3
        assert data.opponent_score   == 1

    def test_zero_zero_draw_is_valid(self):
        """
        TC-P02-B: A 0-0 draw is a legitimate result.

        Verifies that ge=0 allows zero (lower boundary is inclusive).
        """
        data = ChallengeResultSubmit(challenger_score=0, opponent_score=0)

        assert data.challenger_score == 0
        assert data.opponent_score   == 0

    def test_max_score_is_valid(self):
        """
        TC-P02-C: Both scores at 99 (upper boundary) are accepted.
        """
        data = ChallengeResultSubmit(challenger_score=99, opponent_score=99)

        assert data.challenger_score == 99

    def test_negative_challenger_score_raises(self):
        """
        TC-P02-D: A negative challenger score violates the ge=0 constraint.
        """
        with pytest.raises(ValidationError) as exc_info:
            ChallengeResultSubmit(challenger_score=-1, opponent_score=0)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("challenger_score",) for e in errors)

    def test_negative_opponent_score_raises(self):
        """
        TC-P02-E: A negative opponent score violates the ge=0 constraint.
        """
        with pytest.raises(ValidationError) as exc_info:
            ChallengeResultSubmit(challenger_score=0, opponent_score=-5)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("opponent_score",) for e in errors)

    def test_score_exceeds_maximum_raises(self):
        """
        TC-P02-F: A score of 100 violates the le=99 upper-bound constraint.
        """
        with pytest.raises(ValidationError) as exc_info:
            ChallengeResultSubmit(challenger_score=100, opponent_score=0)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("challenger_score",) for e in errors)

    def test_missing_both_scores_raises(self):
        """
        TC-P02-G: Both score fields are required; omitting them raises
        ValidationError with two error entries.
        """
        with pytest.raises(ValidationError) as exc_info:
            ChallengeResultSubmit()

        errors = exc_info.value.errors()
        field_names = {e["loc"][0] for e in errors}
        assert "challenger_score" in field_names
        assert "opponent_score"   in field_names

    @pytest.mark.parametrize("c_score,o_score", [
        (0,  99),
        (99, 0),
        (1,  1),
        (7,  3),
    ])
    def test_various_valid_scores(self, c_score, o_score):
        """
        TC-P02-H: Parametrized sweep over representative valid scorelines.
        """
        data = ChallengeResultSubmit(
            challenger_score=c_score,
            opponent_score=o_score,
        )
        assert data.challenger_score == c_score
        assert data.opponent_score   == o_score


# =============================================================================
# TC-P03  ChallengeStatus — enum normalisation
# =============================================================================

class TestChallengeStatusEnum:

    @pytest.mark.parametrize("value,expected", [
        ("pending",   ChallengeStatus.PENDING),
        ("accepted",  ChallengeStatus.ACCEPTED),
        ("rejected",  ChallengeStatus.REJECTED),
        ("completed", ChallengeStatus.COMPLETED),
        ("cancelled", ChallengeStatus.CANCELLED),
    ])
    def test_lowercase_values_resolve_correctly(self, value, expected):
        """
        TC-P03-A: All declared lowercase enum values map to the correct member.

        The database stores and the API accepts lowercase strings.
        """
        assert ChallengeStatus(value) == expected

    @pytest.mark.parametrize("legacy_value,expected", [
        ("PENDING",   ChallengeStatus.PENDING),
        ("ACCEPTED",  ChallengeStatus.ACCEPTED),
        ("REJECTED",  ChallengeStatus.REJECTED),
        ("COMPLETED", ChallengeStatus.COMPLETED),
        ("CANCELLED", ChallengeStatus.CANCELLED),
    ])
    def test_uppercase_legacy_values_normalised_via_missing(self, legacy_value, expected):
        """
        TC-P03-B: Legacy UPPERCASE enum labels are normalised by _missing_().

        Before migration d4e5f6a7b8c9 the DB stored uppercase labels.
        The _missing_() hook ensures backward compatibility with any rows
        that pre-date the migration.
        """
        result = ChallengeStatus(legacy_value)
        assert result == expected

    def test_invalid_enum_value_returns_none_from_missing(self):
        """
        TC-P03-C: An unrecognised string returns None from _missing_().

        Python will then raise ValueError; this verifies the guard behaviour.
        """
        with pytest.raises(ValueError):
            ChallengeStatus("invalid_status")

    def test_enum_values_are_lowercase_strings(self):
        """
        TC-P03-D: Every member's .value is a lowercase string.

        This invariant is required for the SQLAlchemy native_enum=False
        column and the PostgreSQL enum type (post-migration).
        """
        for member in ChallengeStatus:
            assert member.value == member.value.lower()
            assert isinstance(member.value, str)


# =============================================================================
# TC-P04  ChallengeResponse — ORM serialisation
# =============================================================================

class TestChallengeResponseSerialisation:
    """
    These tests construct minimal ORM-like objects and verify that
    ChallengeResponse.model_validate() maps them correctly.

    No database session is required — a plain Python namespace is used
    to simulate the ORM object, which is valid because model_validate
    with from_attributes=True calls getattr() on the passed object.
    """

    class _FakeTeam:
        """Minimal stand-in for a Team ORM object."""
        def __init__(self, id_, name, city=None, rating=1000):
            self.id     = id_
            self.name   = name
            self.city   = city
            self.rating = rating

    class _FakeChallenge:
        """Minimal stand-in for a Challenge ORM object."""
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    def _make_challenge(self, **overrides):
        defaults = dict(
            id=1,
            challenger_id=10,
            opponent_id=20,
            status=ChallengeStatus.PENDING,
            match_date=None,
            location=None,
            challenger_score=None,
            opponent_score=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            challenger=None,
            opponent=None,
        )
        defaults.update(overrides)
        return self._FakeChallenge(**defaults)

    def test_pending_challenge_serialises_correctly(self):
        """
        TC-P04-A: A PENDING challenge with no scores serialises without errors.

        Verifies that optional nullable fields (scores, dates) are
        correctly represented as None in the response schema.
        """
        fake = self._make_challenge()
        response = ChallengeResponse.model_validate(fake)

        assert response.id             == 1
        assert response.status         == ChallengeStatus.PENDING
        assert response.challenger_score is None
        assert response.opponent_score   is None

    def test_completed_challenge_includes_scores(self):
        """
        TC-P04-B: A COMPLETED challenge with recorded scores serialises both.
        """
        fake = self._make_challenge(
            status=ChallengeStatus.COMPLETED,
            challenger_score=3,
            opponent_score=1,
        )
        response = ChallengeResponse.model_validate(fake)

        assert response.status           == ChallengeStatus.COMPLETED
        assert response.challenger_score == 3
        assert response.opponent_score   == 1

    def test_team_brief_nested_in_response(self):
        """
        TC-P04-C: Nested team objects are serialised via TeamBrief schema.
        """
        team_a = self._FakeTeam(id_=10, name="Team Alpha", city="Nitra")
        team_b = self._FakeTeam(id_=20, name="Team Beta",  city="Bratislava")
        fake   = self._make_challenge(challenger=team_a, opponent=team_b)

        response = ChallengeResponse.model_validate(fake)

        assert response.challenger is not None
        assert response.challenger.id   == 10
        assert response.challenger.name == "Team Alpha"
        assert response.opponent  is not None
        assert response.opponent.city   == "Bratislava"

    def test_use_enum_values_serialises_to_string(self):
        """
        TC-P04-D: model_dump() returns the enum's string value, not the member.

        ChallengeResponse declares use_enum_values=True so JSON payloads
        contain "pending" not ChallengeStatus.PENDING.
        """
        fake = self._make_challenge(status=ChallengeStatus.ACCEPTED)
        response = ChallengeResponse.model_validate(fake)
        dumped   = response.model_dump()

        assert dumped["status"] == "accepted"
        assert isinstance(dumped["status"], str)
