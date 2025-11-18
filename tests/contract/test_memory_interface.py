"""Contract tests for Memory interface."""

import pytest

from aeon.exceptions import MemoryError
from aeon.memory.interface import Memory
from aeon.memory.kv_store import InMemoryKVStore


class TestMemoryInterface:
    """Contract tests verifying Memory interface compliance."""

    @pytest.fixture
    def memory(self):
        """Create memory instance for testing."""
        return InMemoryKVStore()

    def test_memory_has_write_method(self, memory):
        """Test that Memory implementation has write() method."""
        assert hasattr(memory, "write")
        assert callable(memory.write)

    def test_memory_has_read_method(self, memory):
        """Test that Memory implementation has read() method."""
        assert hasattr(memory, "read")
        assert callable(memory.read)

    def test_memory_has_search_method(self, memory):
        """Test that Memory implementation has search() method."""
        assert hasattr(memory, "search")
        assert callable(memory.search)

    def test_write_stores_value(self, memory):
        """Test that write() stores a value."""
        memory.write("test_key", "test_value")
        assert memory.read("test_key") == "test_value"

    def test_read_retrieves_stored_value(self, memory):
        """Test that read() retrieves stored value."""
        memory.write("key1", "value1")
        result = memory.read("key1")
        assert result == "value1"

    def test_read_returns_none_for_missing_key(self, memory):
        """Test that read() returns None for missing key."""
        result = memory.read("nonexistent")
        assert result is None

    def test_write_raises_error_for_invalid_key(self, memory):
        """Test that write() raises MemoryError for invalid key."""
        with pytest.raises(MemoryError):
            memory.write("", "value")  # Empty key
        
        with pytest.raises(MemoryError):
            memory.write(None, "value")  # None key

    def test_search_finds_keys_by_prefix(self, memory):
        """Test that search() finds keys by prefix."""
        memory.write("user_name", "Alice")
        memory.write("user_age", 30)
        memory.write("other_key", "value")
        
        results = memory.search("user_")
        assert len(results) == 2
        keys = [key for key, _ in results]
        assert "user_name" in keys
        assert "user_age" in keys
        assert "other_key" not in keys

    def test_search_returns_empty_list_for_no_matches(self, memory):
        """Test that search() returns empty list when no matches."""
        memory.write("key1", "value1")
        results = memory.search("nonexistent_prefix")
        assert results == []

    def test_search_is_case_sensitive(self, memory):
        """Test that search() is case-sensitive."""
        memory.write("User_Name", "Alice")
        results = memory.search("user_")
        assert len(results) == 0  # Case-sensitive, so no match

