"""
Team API Endpoints - REFACTORED VERSION

This is the refactored version demonstrating Clean Architecture principles:
- Controllers handle HTTP concerns only
- Business logic moved to TeamService
- Custom exceptions instead of HTTPException
- Consistent error responses via global exception handler
- Database query optimization with eager loading
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.models.user import UserRole
from app.services.team_service import TeamService


router = APIRouter()


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_team_service(db: Session = Depends(deps.get_db)) -> TeamService:
    """
    Dependency injection for TeamService

    Provides a TeamService instance with database session
    """
    return TeamService(db)


# ============================================================================
# TEAM CRUD ENDPOINTS
# ============================================================================


@router.get("/", response_model=List[schemas.Team])
def get_teams(
    *,
    skip: int = 0,
    limit: int = 100,
    team_service: TeamService = Depends(get_team_service)
) -> List[models.Team]:
    """
    Retrieve teams with pagination

    **Optimizations:**
    - Eager loading of captain relationship (prevents N+1 queries)
    - Pagination support

    **Query Example:**
    ```
    GET /api/v1/teams?skip=0&limit=20
    ```
    """
    # Service handles business logic and database optimization
    teams = team_service.get_teams(
        skip=skip,
        limit=limit,
        eager_load_captain=True  # Optimized query
    )
    return teams


@router.get("/{team_id}", response_model=schemas.Team)
def get_team(
    *,
    team_id: int,
    team_service: TeamService = Depends(get_team_service)
) -> models.Team:
    """
    Get team by ID

    **Raises:**
    - 404: Team not found (TeamNotFoundError)

    **Optimizations:**
    - Eager loading of captain relationship
    """
    # Service handles existence check and raises TeamNotFoundError if not found
    # Global exception handler converts to 404 response
    team = team_service.get_team_by_id(team_id, eager_load_captain=True)
    return team


@router.post("/", response_model=schemas.Team, status_code=status.HTTP_201_CREATED)
def create_team(
    *,
    team_in: schemas.TeamCreate,
    current_user: models.User = Depends(deps.require_role(UserRole.CAPTAIN)),
    team_service: TeamService = Depends(get_team_service)
) -> models.Team:
    """
    Create a new team (Captain only)

    **Business Rules (enforced by service layer):**
    - Each captain can only create one team
    - Team name must be unique

    **Raises:**
    - 400: Captain already has team (CaptainAlreadyHasTeamError)
    - 400: Team name already exists (TeamNameAlreadyExistsError)
    - 403: User is not a captain (handled by dependency)

    **Example:**
    ```json
    {
      "name": "Thunder FC",
      "description": "Best team in Prague",
      "city": "Prague"
    }
    ```
    """
    # Service handles all business logic validation
    # Custom exceptions are raised and handled by global exception handler
    team = team_service.create_team(team_in=team_in, captain_id=current_user.id)
    return team


@router.put("/{team_id}", response_model=schemas.Team)
def update_team(
    *,
    team_id: int,
    team_in: schemas.TeamUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
) -> models.Team:
    """
    Update team (Owner only)

    **Business Rules (enforced by service layer):**
    - Only team captain can update
    - Team name must remain unique if changed

    **Raises:**
    - 404: Team not found (TeamNotFoundError)
    - 403: Not team owner (NotTeamOwnerError)
    - 400: Team name already exists (TeamNameAlreadyExistsError)

    **Example:**
    ```json
    {
      "description": "Updated description",
      "city": "Brno"
    }
    ```
    """
    # Service handles ownership verification and update logic
    team = team_service.update_team(
        team_id=team_id,
        team_in=team_in,
        current_user_id=current_user.id
    )
    return team


@router.delete("/{team_id}", response_model=schemas.Team)
def delete_team(
    *,
    team_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
) -> models.Team:
    """
    Delete team (Owner only)

    **Business Rules (enforced by service layer):**
    - Only team captain can delete

    **Raises:**
    - 404: Team not found (TeamNotFoundError)
    - 403: Not team owner (NotTeamOwnerError)
    """
    # Service handles ownership verification and deletion
    team = team_service.delete_team(team_id=team_id, current_user_id=current_user.id)
    return team


@router.get("/my/team", response_model=schemas.Team)
def get_my_team(
    *,
    current_user: models.User = Depends(deps.require_role(UserRole.CAPTAIN)),
    team_service: TeamService = Depends(get_team_service)
) -> models.Team:
    """
    Get current user's team (Captain only)

    **Raises:**
    - 404: Captain has no team (TeamNotFoundError)
    - 403: User is not a captain (handled by dependency)
    """
    team = team_service.get_user_team(user_id=current_user.id)

    # If captain has no team, raise TeamNotFoundError
    if not team:
        from app.core.exceptions import TeamNotFoundError
        raise TeamNotFoundError(f"captain_{current_user.id}")

    return team


# ============================================================================
# SEARCH & FILTERING (NEW)
# ============================================================================


@router.get("/search/", response_model=List[schemas.Team])
def search_teams(
    *,
    q: str,
    skip: int = 0,
    limit: int = 100,
    team_service: TeamService = Depends(get_team_service)
) -> List[models.Team]:
    """
    Search teams by name or description

    **Query Parameters:**
    - q: Search query string
    - skip: Number of results to skip (pagination)
    - limit: Maximum results to return

    **Example:**
    ```
    GET /api/v1/teams/search/?q=thunder&skip=0&limit=20
    ```
    """
    teams = team_service.search_teams(query=q, skip=skip, limit=limit)
    return teams


# ============================================================================
# COMPARISON: OLD vs NEW IMPLEMENTATION
# ============================================================================

"""
BEFORE (Old Implementation):
```python
@router.post("/", response_model=schemas.Team)
def create_team(*,
    db: Session = Depends(deps.get_db),
    team_in: schemas.TeamCreate,
    current_user = Depends(deps.require_role(UserRole.CAPTAIN))
):
    # ❌ Business logic mixed in controller
    existing_team = crud.team.get_by_captain(db, captain_id=current_user.id)
    if existing_team:
        raise HTTPException(  # ❌ HTTP exception in business logic
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a team..."
        )

    # ❌ Direct CRUD call from controller
    team = crud.team.create_with_captain(db, obj_in=team_in, captain_id=current_user.id)
    return team
```

AFTER (Refactored):
```python
@router.post("/", response_model=schemas.Team)
def create_team(*,
    team_in: schemas.TeamCreate,
    current_user = Depends(deps.require_role(UserRole.CAPTAIN)),
    team_service: TeamService = Depends(get_team_service)  # ✓ Service injected
):
    # ✓ Business logic in service layer
    # ✓ Custom exceptions instead of HTTPException
    # ✓ Clean separation of concerns
    team = team_service.create_team(team_in=team_in, captain_id=current_user.id)
    return team
```

BENEFITS:
1. ✓ Testable business logic (can test TeamService independently)
2. ✓ No HTTP concerns in business logic
3. ✓ Consistent error handling via exception handler
4. ✓ Database optimization in one place (service)
5. ✓ Single Responsibility Principle followed
6. ✓ Easier to add new business rules
7. ✓ Better code organization and maintainability
"""
