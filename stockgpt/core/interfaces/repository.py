"""
Repository Interface

Generic repository pattern for data access abstraction.
Enables easy swapping between database, in-memory, or mock implementations.
"""

from typing import Protocol, TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime

# Generic type for entities
T = TypeVar('T')


class IRepository(Protocol[T]):
    """
    Generic repository interface for data persistence.

    Type parameter T represents the entity type (Signal, Stock, Pattern, etc.)
    """

    async def save(self, entity: T) -> T:
        """
        Save or update an entity.

        Args:
            entity: Entity to save

        Returns:
            Saved entity with updated metadata (id, timestamps)
        """
        ...

    async def find_by_id(self, entity_id: str) -> Optional[T]:
        """
        Find entity by unique identifier.

        Args:
            entity_id: Unique identifier

        Returns:
            Entity if found, None otherwise
        """
        ...

    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[T]:
        """
        Find all entities with pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """
        ...

    async def find_by_criteria(
        self,
        criteria: Dict[str, Any],
        limit: Optional[int] = None,
    ) -> List[T]:
        """
        Find entities matching search criteria.

        Args:
            criteria: Dictionary of field:value pairs
            limit: Maximum results to return

        Returns:
            List of matching entities
        """
        ...

    async def delete(self, entity_id: str) -> bool:
        """
        Delete entity by identifier.

        Args:
            entity_id: Entity to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    async def delete_many(self, criteria: Dict[str, Any]) -> int:
        """
        Delete multiple entities matching criteria.

        Args:
            criteria: Deletion criteria

        Returns:
            Number of entities deleted
        """
        ...

    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching criteria.

        Args:
            criteria: Optional filter criteria

        Returns:
            Count of matching entities
        """
        ...

    async def exists(self, entity_id: str) -> bool:
        """
        Check if entity exists.

        Args:
            entity_id: Entity identifier

        Returns:
            True if exists, False otherwise
        """
        ...