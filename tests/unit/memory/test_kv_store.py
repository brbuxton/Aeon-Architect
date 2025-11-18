"""Unit tests for InMemoryKVStore."""

import pytest

from aeon.exceptions import MemoryError
from aeon.memory.kv_store import InMemoryKVStore


class TestInMemoryKVStore:
    """Test InMemoryKVStore implementation."""

    def test_write_and_read(self):
        """Test basic write and read operations."""
        store = InMemoryKVStore()
        store.write("key1", "value1")
        assert store.read("key1") == "value1"

    def test_write_overwrites_existing_key(self):
        """Test that write() overwrites existing key."""
        store = InMemoryKVStore()
        store.write("key1", "value1")
        store.write("key1", "value2")
        assert store.read("key1") == "value2"

    def test_read_returns_none_for_missing_key(self):
        """Test that read() returns None for missing key."""
        store = InMemoryKVStore()
        assert store.read("nonexistent") is None

    def test_write_raises_error_for_empty_key(self):
        """Test that write() raises MemoryError for empty key."""
        store = InMemoryKVStore()
        with pytest.raises(MemoryError, match="non-empty string"):
            store.write("", "value")

    def test_write_raises_error_for_non_string_key(self):
        """Test that write() raises MemoryError for non-string key."""
        store = InMemoryKVStore()
        with pytest.raises(MemoryError, match="non-empty string"):
            store.write(123, "value")  # type: ignore

    def test_read_raises_error_for_empty_key(self):
        """Test that read() raises MemoryError for empty key."""
        store = InMemoryKVStore()
        with pytest.raises(MemoryError, match="non-empty string"):
            store.read("")

    def test_read_raises_error_for_non_string_key(self):
        """Test that read() raises MemoryError for non-string key."""
        store = InMemoryKVStore()
        with pytest.raises(MemoryError, match="non-empty string"):
            store.read(123)  # type: ignore

    def test_search_finds_keys_by_prefix(self):
        """Test that search() finds keys by prefix."""
        store = InMemoryKVStore()
        store.write("user_name", "Alice")
        store.write("user_age", 30)
        store.write("other_key", "value")
        
        results = store.search("user_")
        assert len(results) == 2
        # Check that results are tuples of (key, value)
        assert ("user_name", "Alice") in results
        assert ("user_age", 30) in results

    def test_search_returns_empty_list_for_no_matches(self):
        """Test that search() returns empty list when no matches."""
        store = InMemoryKVStore()
        store.write("key1", "value1")
        results = store.search("nonexistent")
        assert results == []

    def test_search_is_case_sensitive(self):
        """Test that search() is case-sensitive."""
        store = InMemoryKVStore()
        store.write("User_Name", "Alice")
        results = store.search("user_")
        assert len(results) == 0

    def test_search_raises_error_for_non_string_prefix(self):
        """Test that search() raises MemoryError for non-string prefix."""
        store = InMemoryKVStore()
        with pytest.raises(MemoryError, match="must be a string"):
            store.search(123)  # type: ignore

    def test_store_multiple_types(self):
        """Test that store can handle multiple value types."""
        store = InMemoryKVStore()
        store.write("string", "text")
        store.write("number", 42)
        store.write("list", [1, 2, 3])
        store.write("dict", {"key": "value"})
        
        assert store.read("string") == "text"
        assert store.read("number") == 42
        assert store.read("list") == [1, 2, 3]
        assert store.read("dict") == {"key": "value"}

    def test_search_with_empty_prefix_returns_all(self):
        """Test that search with empty prefix returns all keys."""
        store = InMemoryKVStore()
        store.write("key1", "value1")
        store.write("key2", "value2")
        
        results = store.search("")
        assert len(results) == 2

