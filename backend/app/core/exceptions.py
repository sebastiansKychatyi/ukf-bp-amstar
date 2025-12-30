"""
Custom Exception Classes for AmStar Platform

This module defines a hierarchy of custom exceptions that separate
business logic errors from HTTP concerns, making the code more testable
and maintainable.
"""

from typing import Any, Optional


class AmStarException(Exception):
    """Base exception for all AmStar business logic errors"""

    def __init__(self, message: str, error_code: Optional[str] = None, **kwargs: Any):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = kwargs
        super().__init__(self.message)


# ============================================================================
# AUTHENTICATION & AUTHORIZATION EXCEPTIONS
# ============================================================================


class AuthenticationError(AmStarException):
    """Raised when authentication fails"""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""

    def __init__(self):
        super().__init__(
            message="Incorrect email or password",
            error_code="INVALID_CREDENTIALS"
        )


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""

    def __init__(self):
        super().__init__(
            message="Token has expired",
            error_code="TOKEN_EXPIRED"
        )


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""

    def __init__(self, reason: str = "Invalid token"):
        super().__init__(
            message=reason,
            error_code="INVALID_TOKEN"
        )


class InsufficientPermissionsError(AmStarException):
    """Raised when user lacks required permissions"""

    def __init__(self, required_role: Optional[str] = None):
        message = "Insufficient permissions to perform this action"
        if required_role:
            message = f"This action requires {required_role} role"

        super().__init__(
            message=message,
            error_code="INSUFFICIENT_PERMISSIONS",
            required_role=required_role
        )


# ============================================================================
# RESOURCE EXCEPTIONS
# ============================================================================


class ResourceNotFoundError(AmStarException):
    """Raised when a requested resource doesn't exist"""

    def __init__(self, resource_type: str, identifier: Any):
        super().__init__(
            message=f"{resource_type} with identifier '{identifier}' not found",
            error_code="RESOURCE_NOT_FOUND",
            resource_type=resource_type,
            identifier=str(identifier)
        )


class TeamNotFoundError(ResourceNotFoundError):
    """Raised when team doesn't exist"""

    def __init__(self, team_id: Any):
        super().__init__(resource_type="Team", identifier=team_id)


class UserNotFoundError(ResourceNotFoundError):
    """Raised when user doesn't exist"""

    def __init__(self, user_id: Any):
        super().__init__(resource_type="User", identifier=user_id)


class ChallengeNotFoundError(ResourceNotFoundError):
    """Raised when challenge doesn't exist"""

    def __init__(self, challenge_id: Any):
        super().__init__(resource_type="Challenge", identifier=challenge_id)


# ============================================================================
# BUSINESS RULE VIOLATIONS
# ============================================================================


class BusinessRuleViolationError(AmStarException):
    """Base exception for business rule violations"""

    pass


class DuplicateResourceError(BusinessRuleViolationError):
    """Raised when attempting to create a duplicate resource"""

    def __init__(self, resource_type: str, field: str, value: Any):
        super().__init__(
            message=f"{resource_type} with {field} '{value}' already exists",
            error_code="DUPLICATE_RESOURCE",
            resource_type=resource_type,
            field=field,
            value=str(value)
        )


class EmailAlreadyExistsError(DuplicateResourceError):
    """Raised when email is already registered"""

    def __init__(self, email: str):
        super().__init__(resource_type="User", field="email", value=email)


class UsernameAlreadyExistsError(DuplicateResourceError):
    """Raised when username is already taken"""

    def __init__(self, username: str):
        super().__init__(resource_type="User", field="username", value=username)


class TeamNameAlreadyExistsError(DuplicateResourceError):
    """Raised when team name is already taken"""

    def __init__(self, name: str):
        super().__init__(resource_type="Team", field="name", value=name)


class CaptainAlreadyHasTeamError(BusinessRuleViolationError):
    """Raised when captain tries to create multiple teams"""

    def __init__(self):
        super().__init__(
            message="You already have a team. Each captain can only create one team.",
            error_code="CAPTAIN_ALREADY_HAS_TEAM"
        )


class NotTeamOwnerError(BusinessRuleViolationError):
    """Raised when user tries to modify a team they don't own"""

    def __init__(self):
        super().__init__(
            message="You can only modify your own team",
            error_code="NOT_TEAM_OWNER"
        )


class InvalidChallengeStatusError(BusinessRuleViolationError):
    """Raised when challenge status transition is invalid"""

    def __init__(self, current_status: str, attempted_status: str):
        super().__init__(
            message=f"Cannot change challenge status from {current_status} to {attempted_status}",
            error_code="INVALID_STATUS_TRANSITION",
            current_status=current_status,
            attempted_status=attempted_status
        )


class SelfChallengeError(BusinessRuleViolationError):
    """Raised when team tries to challenge itself"""

    def __init__(self):
        super().__init__(
            message="A team cannot challenge itself",
            error_code="SELF_CHALLENGE_NOT_ALLOWED"
        )


class TeamNotActiveError(BusinessRuleViolationError):
    """Raised when operation requires active team"""

    def __init__(self, team_id: Any):
        super().__init__(
            message=f"Team {team_id} is not active",
            error_code="TEAM_NOT_ACTIVE",
            team_id=str(team_id)
        )


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================


class ValidationError(AmStarException):
    """Raised when input validation fails"""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error on field '{field}': {message}",
            error_code="VALIDATION_ERROR",
            field=field
        )


class InvalidRatingError(ValidationError):
    """Raised when rating value is invalid"""

    def __init__(self, rating: int):
        super().__init__(
            field="rating",
            message=f"Rating {rating} is outside valid range (0-5000)"
        )


class InvalidDateError(ValidationError):
    """Raised when date value is invalid"""

    def __init__(self, field: str, reason: str):
        super().__init__(field=field, message=reason)


# ============================================================================
# EXTERNAL SERVICE EXCEPTIONS
# ============================================================================


class ExternalServiceError(AmStarException):
    """Raised when external service call fails"""

    def __init__(self, service_name: str, reason: str):
        super().__init__(
            message=f"External service '{service_name}' error: {reason}",
            error_code="EXTERNAL_SERVICE_ERROR",
            service_name=service_name
        )


class EmailServiceError(ExternalServiceError):
    """Raised when email service fails"""

    def __init__(self, reason: str):
        super().__init__(service_name="EmailService", reason=reason)


class RedisServiceError(ExternalServiceError):
    """Raised when Redis operation fails"""

    def __init__(self, reason: str):
        super().__init__(service_name="Redis", reason=reason)


# ============================================================================
# RATE LIMITING EXCEPTIONS
# ============================================================================


class RateLimitExceededError(AmStarException):
    """Raised when rate limit is exceeded"""

    def __init__(self, limit: int, window: int):
        super().__init__(
            message=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds",
            error_code="RATE_LIMIT_EXCEEDED",
            limit=limit,
            window=window
        )
