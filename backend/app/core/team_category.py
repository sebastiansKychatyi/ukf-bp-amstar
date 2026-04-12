"""
Team experience tiers and dynamic K-factor for the ELO rating system.

Tiers: PROVISIONAL (<10 matches, K=40), DEVELOPING (10-29, K=30), ESTABLISHED (≥30, K=20).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


# Thresholds (single source of truth — also imported by EloService)

PROVISIONAL_MAX_MATCHES: int = 10   # 0 – 9 matches  → PROVISIONAL
DEVELOPING_MAX_MATCHES: int = 30    # 10 – 29 matches → DEVELOPING
                                    # 30+             → ESTABLISHED


# Enum

class TeamCategory(str, enum.Enum):
    """Experience tier of a team based on completed matches played."""

    PROVISIONAL = "provisional"
    DEVELOPING  = "developing"
    ESTABLISHED = "established"


# Internal metadata table

@dataclass(frozen=True)
class _CategoryMeta:
    label_en: str
    label_sk: str
    k_factor: int


_META: dict[TeamCategory, _CategoryMeta] = {
    TeamCategory.PROVISIONAL: _CategoryMeta(
        label_en="Provisional Team",
        label_sk="Provisorný tím",
        k_factor=40,
    ),
    TeamCategory.DEVELOPING: _CategoryMeta(
        label_en="Developing Team",
        label_sk="Rozvíjajúci tím",
        k_factor=30,
    ),
    TeamCategory.ESTABLISHED: _CategoryMeta(
        label_en="Established Team",
        label_sk="Etablovaný tím",
        k_factor=20,
    ),
}


# Public result type

@dataclass(frozen=True)
class TeamCategoryInfo:
    """Fully resolved category information for a team."""

    category: TeamCategory
    label_en: str
    label_sk: str
    k_factor: int
    matches_played: int


# Public function

def get_team_category(matches_played: int) -> TeamCategoryInfo:
    """
    Determine a team's experience category and base K-factor.

    Args:
        matches_played: Number of completed matches the team has played.

    Returns:
        A frozen :class:`TeamCategoryInfo` dataclass.

    Raises:
        ValueError: If *matches_played* is negative.

    Examples::

        >>> get_team_category(0).category
        <TeamCategory.PROVISIONAL: 'provisional'>
        >>> get_team_category(15).k_factor
        30
        >>> get_team_category(30).label_sk
        'Etablovaný tím'
    """
    if matches_played < 0:
        raise ValueError(
            f"matches_played must be non-negative, got {matches_played}"
        )

    if matches_played < PROVISIONAL_MAX_MATCHES:
        cat = TeamCategory.PROVISIONAL
    elif matches_played < DEVELOPING_MAX_MATCHES:
        cat = TeamCategory.DEVELOPING
    else:
        cat = TeamCategory.ESTABLISHED

    meta = _META[cat]
    return TeamCategoryInfo(
        category=cat,
        label_en=meta.label_en,
        label_sk=meta.label_sk,
        k_factor=meta.k_factor,
        matches_played=matches_played,
    )
