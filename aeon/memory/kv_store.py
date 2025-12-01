"""In-memory key/value store implementation."""

from typing import Any, List, Optional, Tuple

from aeon.exceptions import MemoryError
from aeon.memory.interface import Memory


class InMemoryKVStore(Memory):
    """Simple in-memory key/value store."""

    def __init__(self) -> None:
        """Initialize empty store."""
        self._store: dict[str, Any] = {}

    def write(self, key: str, value: Any) -> None:
        """
        Store a value with the given key.

        Args:
            key: Unique identifier (non-empty string)
            value: Value to store (must be serializable)

        Raises:
            MemoryError: On storage failure
        """
        if not key or not isinstance(key, str):
            raise MemoryError("Key must be a non-empty string")
        try:
            self._store[key] = value
        except Exception as e:
            raise MemoryError(f"Failed to write key '{key}': {str(e)}") from e

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
        if not key or not isinstance(key, str):
            raise MemoryError("Key must be a non-empty string")
        try:
            return self._store.get(key)
        except Exception as e:
            raise MemoryError(f"Failed to read key '{key}': {str(e)}") from e

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
        if not isinstance(prefix, str):
            raise MemoryError("Prefix must be a string")
        try:
            results = []
            for key, value in self._store.items():
                if key.startswith(prefix):
                    results.append((key, value))
            return results
        except Exception as e:
            raise MemoryError(f"Failed to search prefix '{prefix}': {str(e)}") from e







