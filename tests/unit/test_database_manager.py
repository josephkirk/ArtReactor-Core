"""Unit tests for Database Manager."""

import pytest

from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)


@pytest.fixture
def database_provider(tmp_path):
    """Create a temporary database provider for testing."""
    db_path = tmp_path / "test_database.db"
    return SqliteDatabaseProvider(str(db_path))


@pytest.fixture
def database_manager(database_provider):
    """Create a database manager with the test provider."""
    return DatabaseManager(database_provider)


def test_set_and_get_data(database_manager):
    """Test storing and retrieving data."""
    test_data = {"name": "Test Asset", "type": "model", "version": 1}

    database_manager.set("assets", "asset_001", test_data)
    retrieved = database_manager.get("assets", "asset_001")

    assert retrieved == test_data


def test_get_nonexistent_data(database_manager):
    """Test retrieving data that doesn't exist returns None."""
    result = database_manager.get("nonexistent", "key123")
    assert result is None


def test_update_existing_data(database_manager):
    """Test updating existing data."""
    original_data = {"name": "Original", "value": 100}
    updated_data = {"name": "Updated", "value": 200}

    database_manager.set("test_collection", "key1", original_data)
    database_manager.set("test_collection", "key1", updated_data)

    retrieved = database_manager.get("test_collection", "key1")
    assert retrieved == updated_data


def test_remove_data(database_manager):
    """Test removing data."""
    test_data = {"item": "test"}

    database_manager.set("collection1", "key1", test_data)
    removed = database_manager.remove("collection1", "key1")

    assert removed is True
    assert database_manager.get("collection1", "key1") is None


def test_remove_nonexistent_data(database_manager):
    """Test removing data that doesn't exist returns False."""
    removed = database_manager.remove("collection1", "nonexistent_key")
    assert removed is False


def test_list_keys(database_manager):
    """Test listing all keys in a collection."""
    database_manager.set("collection1", "key1", {"data": "value1"})
    database_manager.set("collection1", "key2", {"data": "value2"})
    database_manager.set("collection1", "key3", {"data": "value3"})
    database_manager.set("collection2", "key4", {"data": "value4"})

    keys = database_manager.list_keys("collection1")
    assert len(keys) == 3
    assert "key1" in keys
    assert "key2" in keys
    assert "key3" in keys
    assert "key4" not in keys  # From different collection


def test_list_keys_empty_collection(database_manager):
    """Test listing keys in an empty collection returns empty list."""
    keys = database_manager.list_keys("empty_collection")
    assert keys == []


def test_list_collections(database_manager):
    """Test listing all collections."""
    database_manager.set("assets", "key1", {"data": "value1"})
    database_manager.set("projects", "key2", {"data": "value2"})
    database_manager.set("metadata", "key3", {"data": "value3"})

    collections = database_manager.list_collections()
    assert len(collections) == 3
    assert "assets" in collections
    assert "projects" in collections
    assert "metadata" in collections


def test_list_collections_empty_database(database_manager):
    """Test listing collections in an empty database returns empty list."""
    collections = database_manager.list_collections()
    assert collections == []


def test_complex_json_data(database_manager):
    """Test storing and retrieving complex nested JSON data."""
    complex_data = {
        "name": "Complex Asset",
        "metadata": {
            "author": "Artist Name",
            "created": "2024-01-01",
            "tags": ["3d", "character", "rigged"],
        },
        "properties": {
            "polycount": 50000,
            "materials": ["skin", "cloth", "metal"],
            "bones": 150,
        },
        "nested": {"deep": {"very": {"nested": {"value": 42}}}},
    }

    database_manager.set("complex", "asset_complex", complex_data)
    retrieved = database_manager.get("complex", "asset_complex")

    assert retrieved == complex_data
    assert retrieved["metadata"]["tags"] == ["3d", "character", "rigged"]
    assert retrieved["nested"]["deep"]["very"]["nested"]["value"] == 42


def test_collection_isolation(database_manager):
    """Test that collections are properly isolated."""
    data1 = {"collection": "first"}
    data2 = {"collection": "second"}

    # Same key in different collections
    database_manager.set("collection1", "shared_key", data1)
    database_manager.set("collection2", "shared_key", data2)

    # Each collection should have its own data
    assert database_manager.get("collection1", "shared_key") == data1
    assert database_manager.get("collection2", "shared_key") == data2


def test_provider_persistence(tmp_path):
    """Test that data persists across provider instances."""
    db_path = tmp_path / "persistent.db"

    # First provider instance
    provider1 = SqliteDatabaseProvider(str(db_path))
    manager1 = DatabaseManager(provider1)
    manager1.set("test", "key1", {"persisted": "data"})

    # Second provider instance pointing to same database
    provider2 = SqliteDatabaseProvider(str(db_path))
    manager2 = DatabaseManager(provider2)
    retrieved = manager2.get("test", "key1")

    assert retrieved == {"persisted": "data"}


def test_special_characters_in_keys(database_manager):
    """Test handling special characters in keys."""
    special_keys = [
        "key-with-dashes",
        "key_with_underscores",
        "key.with.dots",
        "key:with:colons",
        "key/with/slashes",
    ]

    for key in special_keys:
        database_manager.set("special", key, {"key_name": key})

    for key in special_keys:
        retrieved = database_manager.get("special", key)
        assert retrieved == {"key_name": key}


def test_empty_data_object(database_manager):
    """Test storing and retrieving an empty data object."""
    empty_data = {}
    database_manager.set("test", "empty", empty_data)
    retrieved = database_manager.get("test", "empty")

    assert retrieved == empty_data


def test_unicode_in_data(database_manager):
    """Test handling Unicode characters in data."""
    unicode_data = {
        "name": "Asset名前",
        "description": "这是一个资产",
        "emoji": "🎨🎮🎯",
    }

    database_manager.set("unicode", "key1", unicode_data)
    retrieved = database_manager.get("unicode", "key1")

    assert retrieved == unicode_data


def test_get_all(database_manager):
    """Test retrieving all data from a collection."""
    database_manager.set("collection1", "key1", {"value": 1})
    database_manager.set("collection1", "key2", {"value": 2})
    database_manager.set("collection1", "key3", {"value": 3})
    database_manager.set("collection2", "key4", {"value": 4})

    all_data = database_manager.get_all("collection1")
    assert len(all_data) == 3
    assert "key1" in all_data
    assert "key2" in all_data
    assert "key3" in all_data
    assert "key4" not in all_data  # From different collection
    assert all_data["key1"]["value"] == 1
    assert all_data["key2"]["value"] == 2


def test_get_all_empty_collection(database_manager):
    """Test get_all on empty collection returns empty dict."""
    all_data = database_manager.get_all("empty_collection")
    assert all_data == {}


def test_clear_collection(database_manager):
    """Test clearing all data from a collection."""
    database_manager.set("collection1", "key1", {"data": 1})
    database_manager.set("collection1", "key2", {"data": 2})
    database_manager.set("collection2", "key3", {"data": 3})

    # Clear collection1
    removed = database_manager.clear_collection("collection1")
    assert removed == 2

    # Verify collection1 is empty
    assert database_manager.get_all("collection1") == {}
    assert database_manager.list_keys("collection1") == []

    # Verify collection2 is unaffected
    assert database_manager.get("collection2", "key3") is not None


def test_clear_empty_collection(database_manager):
    """Test clearing empty collection returns 0."""
    removed = database_manager.clear_collection("nonexistent")
    assert removed == 0


def test_non_serializable_data(database_manager):
    """Test that non-serializable data raises appropriate error."""
    import datetime

    # Try to store a non-serializable object (function)
    non_serializable_data = {"function": lambda x: x, "date": datetime.datetime.now()}

    with pytest.raises(TypeError) as exc_info:
        database_manager.set("test", "bad_data", non_serializable_data)

    assert "JSON-serializable" in str(exc_info.value)


def test_corrupted_data_handling(database_provider, tmp_path):
    """Test that corrupted data is handled gracefully."""
    import sqlite3

    # Manually insert corrupted JSON data
    with sqlite3.connect(database_provider.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO data_store (collection, key, data) VALUES (?, ?, ?)",
            ("test", "corrupted", "this is not valid JSON {{{"),
        )
        conn.commit()

    # Create manager with the same provider
    manager = DatabaseManager(database_provider)

    # Should return None instead of crashing
    result = manager.get("test", "corrupted")
    assert result is None
