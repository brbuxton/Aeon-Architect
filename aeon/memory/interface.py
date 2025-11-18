"""Memory interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from aeon.exceptions import MemoryError


class Memory(ABC):
    """Abstract interface for memory storage."""

    @abstractmethod
    def write(self, key: str, value: Any) -> None:
        """
        Store a value with the given key.

        Args:
            key: Unique identifier (non-empty string)
            value: Value to store (must be serializable)

        Raises:
            MemoryError: On storage failure
        """
        pass

    @abstractmethod
    def read(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.

        Args:
            key: Identifier to look up

        Returns:
            Stored value or None if key not found

        Raises:
            MemoryError: On read failure
        """
        pass

    @abstractmethod
    def search(self, prefix: str) -> List[Tuple[str, Any]]:
        """
        Find all keys starting with the given prefix.

        Args:
            prefix: Prefix to match

        Returns:
            List of (key, value) tuples for matching keys

        Raises:
            MemoryError: On search failure
        """
        pass


