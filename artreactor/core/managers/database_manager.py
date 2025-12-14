"""Database Manager for ArtReactor Core.

This module provides a simple key-value database interface with support for
multiple backend providers. Other systems and plugins can store and query
JSON-like data through a simple interface.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class DatabaseProvider(ABC):
    """Abstract interface for database providers."""

    @abstractmethod
    def set(self, collection: str, key: str, data: Dict[str, Any]) -> None:
        """Store or update data in the specified collection.

        Args:
            collection: The collection/table name
            key: The unique key for the data
            data: JSON-like dictionary data to store
        """
        pass

    @abstractmethod
    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from the specified collection.

        Args:
            collection: The collection/table name
            key: The unique key for the data

        Returns:
            The stored data as a dictionary, or None if not found
        """
        pass

    @abstractmethod
    def remove(self, collection: str, key: str) -> bool:
        """Remove data from the specified collection.

        Args:
            collection: The collection/table name
            key: The unique key for the data

        Returns:
            True if data was removed, False if key didn't exist
        """
        pass

    @abstractmethod
    def list_keys(self, collection: str) -> List[str]:
        """List all keys in a collection.

        Args:
            collection: The collection/table name

        Returns:
            List of all keys in the collection
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all collections in the database.

        Returns:
            List of all collection names
        """
        pass

    @abstractmethod
    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all data from a collection.

        Args:
            collection: The collection/table name

        Returns:
            Dictionary mapping keys to their data
        """
        pass

    @abstractmethod
    def clear_collection(self, collection: str) -> int:
        """Clear all data from a collection.

        Args:
            collection: The collection/table name

        Returns:
            Number of items removed
        """
        pass


class SqliteDatabaseProvider(DatabaseProvider):
    """SQLite-based database provider for storing JSON-like data."""

    def __init__(self, db_path: str = ".artreactor/database.db"):
        """Initialize the SQLite database provider.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_store (
                    collection TEXT NOT NULL,
                    key TEXT NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY (collection, key)
                )
            """)
            conn.commit()

    def set(self, collection: str, key: str, data: Dict[str, Any]) -> None:
        """Store or update data in the specified collection.

        Raises:
            TypeError: If data contains non-JSON-serializable objects
        """
        # Serialize data to JSON
        try:
            data_json = json.dumps(data)
        except (TypeError, ValueError) as e:
            raise TypeError(
                f"Data must be JSON-serializable. Failed to serialize data for "
                f"collection '{collection}', key '{key}': {e}"
            ) from e

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO data_store (collection, key, data) VALUES (?, ?, ?)",
                (collection, key, data_json),
            )
            conn.commit()

    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from the specified collection.

        Returns:
            The stored data as a dictionary, or None if not found or data is corrupted

        Note:
            If stored data is corrupted and cannot be deserialized, logs a warning
            and returns None instead of raising an exception.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM data_store WHERE collection=? AND key=?",
                (collection, key),
            )
            result = cursor.fetchone()

        if result:
            try:
                return json.loads(result[0])
            except json.JSONDecodeError as e:
                # Log the error but don't crash - corrupted data should not break the system
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to deserialize data for collection '{collection}', "
                    f"key '{key}': {e}. Returning None."
                )
                return None
        return None

    def remove(self, collection: str, key: str) -> bool:
        """Remove data from the specified collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM data_store WHERE collection=? AND key=?",
                (collection, key),
            )
            rows_affected = cursor.rowcount
            conn.commit()

        return rows_affected > 0

    def list_keys(self, collection: str) -> List[str]:
        """List all keys in a collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key FROM data_store WHERE collection=? ORDER BY key",
                (collection,),
            )
            results = cursor.fetchall()

        return [row[0] for row in results]

    def list_collections(self) -> List[str]:
        """List all collections in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT collection FROM data_store ORDER BY collection"
            )
            results = cursor.fetchall()

        return [row[0] for row in results]

    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all data from a collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key, data FROM data_store WHERE collection=?",
                (collection,),
            )
            results = cursor.fetchall()

        data_map = {}
        for key, data_json in results:
            try:
                data_map[key] = json.loads(data_json)
            except json.JSONDecodeError as e:
                # Log and skip corrupted entries
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to deserialize data for collection '{collection}', "
                    f"key '{key}': {e}. Skipping."
                )
                continue
        return data_map

    def clear_collection(self, collection: str) -> int:
        """Clear all data from a collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM data_store WHERE collection=?",
                (collection,),
            )
            rows_affected = cursor.rowcount
            conn.commit()

        return rows_affected


class DatabaseManager:
    """Manager for database operations with pluggable providers.

    Provides a simple interface for plugins and systems to store/query
    JSON-like data across different database backends.
    """

    def __init__(self, provider: DatabaseProvider):
        """Initialize the database manager.

        Args:
            provider: The database provider implementation to use
        """
        self.provider = provider

    def set(self, collection: str, key: str, data: Dict[str, Any]) -> None:
        """Store or update data in the specified collection.

        Args:
            collection: The collection/table name
            key: The unique key for the data
            data: JSON-like dictionary data to store
        """
        self.provider.set(collection, key, data)

    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from the specified collection.

        Args:
            collection: The collection/table name
            key: The unique key for the data

        Returns:
            The stored data as a dictionary, or None if not found
        """
        return self.provider.get(collection, key)

    def remove(self, collection: str, key: str) -> bool:
        """Remove data from the specified collection.

        Args:
            collection: The collection/table name
            key: The unique key for the data

        Returns:
            True if data was removed, False if key didn't exist
        """
        return self.provider.remove(collection, key)

    def list_keys(self, collection: str) -> List[str]:
        """List all keys in a collection.

        Args:
            collection: The collection/table name

        Returns:
            List of all keys in the collection
        """
        return self.provider.list_keys(collection)

    def list_collections(self) -> List[str]:
        """List all collections in the database.

        Returns:
            List of all collection names
        """
        return self.provider.list_collections()

    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all data from a collection.

        Args:
            collection: The collection/table name

        Returns:
            Dictionary mapping keys to their data
        """
        return self.provider.get_all(collection)

    def clear_collection(self, collection: str) -> int:
        """Clear all data from a collection.

        Args:
            collection: The collection/table name

        Returns:
            Number of items removed
        """
        return self.provider.clear_collection(collection)
