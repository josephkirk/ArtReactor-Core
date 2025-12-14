import os
from abc import ABC, abstractmethod
from typing import Optional

from artreactor.models.domain import Secret, SecretScope

# Re-export models for backward compatibility
__all__ = [
    "Secret",
    "SecretScope",
    "SecretProvider",
    "SecretManager",
]


class SecretProvider(ABC):
    """Abstract interface for external secret management services.

    Implementations should connect to services like Hashicorp Vault, AWS Secrets Manager,
    or Azure Key Vault to fetch secrets. The SecretManager will handle caching automatically.
    """

    @abstractmethod
    def get_secret(
        self, key: str, scope: SecretScope, project: Optional[str] = None
    ) -> Optional[Secret]:
        """Get a secret from the external service.

        Args:
            key: Secret key
            scope: Secret scope (USER or PROJECT)
            project: Project name (required for PROJECT scope)

        Returns:
            Secret from the external service, or None if not found
        """
        pass

    @abstractmethod
    def set_secret(self, secret: Secret) -> bool:
        """Set a secret in the external service.

        Args:
            secret: Secret to store

        Returns:
            True if successfully stored, False otherwise
        """
        pass


class SecretManager:
    """Secret Manager with database caching.

    This manager uses a database for caching secrets fetched from
    external services (Hashicorp Vault, AWS Secrets Manager, etc.).
    Each query to the external service is automatically cached in the
    database for faster subsequent access.

    If no external provider is configured, it operates in local-only mode
    using the database as the source of truth, with environment variable fallback.
    """

    CACHE_COLLECTION = "secrets_cache"

    def __init__(self, database_manager, provider: Optional[SecretProvider] = None):
        """Initialize the secret manager.

        Args:
            database_manager: DatabaseManager instance for caching
            provider: Optional external service provider (Vault, AWS, etc.)
        """
        self.db = database_manager
        self.provider = provider

    def _make_cache_key(
        self, key: str, scope: SecretScope, project: Optional[str] = None
    ) -> str:
        """Create a unique cache key for a secret.

        Args:
            key: Secret key
            scope: Secret scope
            project: Project name

        Returns:
            Unique cache key
        """
        project_val = project if scope == SecretScope.PROJECT else ""
        return f"{key}:{scope.value}:{project_val}"

    def get_secret(
        self,
        key: str,
        scope: SecretScope = SecretScope.USER,
        project: Optional[str] = None,
    ) -> Optional[str]:
        """Get a secret by key, using cache or fetching from external service.

        Args:
            key: Secret key
            scope: Secret scope (USER or PROJECT)
            project: Project name (required for PROJECT scope)

        Returns:
            Secret value if found, None otherwise
        """
        cache_key = self._make_cache_key(key, scope, project)

        # Try cache first
        cached = self.db.get(self.CACHE_COLLECTION, cache_key)
        if cached:
            return cached.get("value")

        # If provider exists, get from external service and cache
        if self.provider:
            secret = self.provider.get_secret(key, scope, project)
            if secret:
                self._cache_secret(secret)
                return secret.value

        # Fallback to environment variables for USER scope
        if scope == SecretScope.USER:
            return os.environ.get(key)

        return None

    def set_secret(
        self,
        key: str,
        value: str,
        scope: SecretScope = SecretScope.USER,
        project: Optional[str] = None,
    ) -> bool:
        """Store a secret in cache and optionally in external service.

        Args:
            key: Secret key
            value: Secret value
            scope: Secret scope (USER or PROJECT)
            project: Project name (required for PROJECT scope)

        Returns:
            True if successfully stored
        """
        secret = Secret(key=key, value=value, scope=scope, project=project)

        # If provider exists, set in external service
        if self.provider:
            success = self.provider.set_secret(secret)
            if not success:
                return False

        # Always cache locally
        self._cache_secret(secret)
        return True

    def clear_cache(self):
        """Clear all cached secrets.

        Useful when you want to force a refresh from the external service.
        """
        self.db.clear_collection(self.CACHE_COLLECTION)

    def _cache_secret(self, secret: Secret):
        """Store secret in cache.

        Args:
            secret: Secret to cache
        """
        cache_key = self._make_cache_key(secret.key, secret.scope, secret.project)
        self.db.set(
            self.CACHE_COLLECTION,
            cache_key,
            {
                "key": secret.key,
                "value": secret.value,
                "scope": secret.scope.value,
                "project": secret.project or "",
            },
        )
