"""
Re-export shim — canonical module is app.core.team_category.

The implementation was moved to app/core/ to break a circular import
between the schemas and services packages.  All public names are
re-exported here so that existing imports from app.services.team_category
continue to work unchanged.
"""

from app.core.team_category import (  # noqa: F401
    TeamCategory,
    TeamCategoryInfo,
    get_team_category,
    PROVISIONAL_MAX_MATCHES,
    DEVELOPING_MAX_MATCHES,
)

__all__ = [
    "TeamCategory",
    "TeamCategoryInfo",
    "get_team_category",
    "PROVISIONAL_MAX_MATCHES",
    "DEVELOPING_MAX_MATCHES",
]
