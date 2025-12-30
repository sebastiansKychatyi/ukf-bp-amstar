"""
Base Service Class

Provides common functionality for all service classes including
logging, error handling, and database session management.
"""

from typing import TypeVar, Generic, Optional
from sqlalchemy.orm import Session
from loguru import logger


T = TypeVar("T")


class BaseService(Generic[T]):
    """
    Base service class that all services should inherit from

    Provides:
    - Database session management
    - Common logging patterns
    - Error context handling
    """

    def __init__(self, db: Session):
        """
        Initialize service with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.logger = logger.bind(service=self.__class__.__name__)

    def _log_operation(self, operation: str, **kwargs) -> None:
        """
        Log a service operation

        Args:
            operation: Name of the operation
            **kwargs: Additional context to log
        """
        self.logger.info(f"{operation}", **kwargs)

    def _log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """
        Log an error during a service operation

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
            **kwargs: Additional context to log
        """
        self.logger.error(
            f"{operation} failed: {str(error)}",
            error_type=type(error).__name__,
            **kwargs
        )

    def commit(self) -> None:
        """Commit the current transaction"""
        try:
            self.db.commit()
            self._log_operation("Transaction committed")
        except Exception as e:
            self.db.rollback()
            self._log_error("Transaction commit", e)
            raise

    def rollback(self) -> None:
        """Rollback the current transaction"""
        self.db.rollback()
        self._log_operation("Transaction rolled back")
