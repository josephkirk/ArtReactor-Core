"""Unit tests for SecretManager caching functionality."""

import pytest
from artreactor.core.managers.secret_manager import (
    SecretManager,
    SecretProvider,
    Secret,
    SecretScope,
)
from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)
from typing import Optional


class MockVaultProvider(SecretProvider):
    """Mock external secret management service provider for testing."""

    def __init__(self):
        self.get_calls = []
        self.set_calls = []
        self.secrets = {}

    def get_secret(
        self, key: str, scope: SecretScope, project: Optional[str] = None
    ) -> Optional[Secret]:
        """Simulate getting from external service."""
        self.get_calls.append((key, scope, project))
        cache_key = f"{key}:{scope.value}:{project or ''}"
        return self.secrets.get(cache_key)

    def set_secret(self, secret: Secret) -> bool:
        """Simulate setting to external service."""
        self.set_calls.append(secret)
        cache_key = f"{secret.key}:{secret.scope.value}:{secret.project or ''}"
        self.secrets[cache_key] = secret
        return True

    def add_mock_secret(
        self, key: str, value: str, scope: SecretScope, project: Optional[str] = None
    ):
        """Add a mock secret to the external service."""
        secret = Secret(key=key, value=value, scope=scope, project=project)
        cache_key = f"{key}:{scope.value}:{project or ''}"
        self.secrets[cache_key] = secret


@pytest.fixture
def database_manager(tmp_path):
    """Create a database manager for testing."""
    db_path = tmp_path / "test_secrets_cache.db"
    provider = SqliteDatabaseProvider(str(db_path))
    return DatabaseManager(provider)


@pytest.fixture
def mock_provider():
    """Create a mock external provider."""
    return MockVaultProvider()


def test_cache_miss_fetches_from_provider(database_manager, mock_provider):
    """Test that cache miss triggers get from external provider."""
    # Setup mock provider with a secret
    mock_provider.add_mock_secret("api_key", "secret123", SecretScope.USER)

    sm = SecretManager(database_manager, provider=mock_provider)

    # First call should get from provider
    value = sm.get_secret("api_key", SecretScope.USER)
    assert value == "secret123"
    assert len(mock_provider.get_calls) == 1


def test_cache_hit_skips_provider(database_manager, mock_provider):
    """Test that cache hit doesn't call external provider."""
    # Setup mock provider
    mock_provider.add_mock_secret("cached_key", "cached_value", SecretScope.USER)

    sm = SecretManager(database_manager, provider=mock_provider)

    # First call gets and caches
    sm.get_secret("cached_key", SecretScope.USER)
    assert len(mock_provider.get_calls) == 1

    # Second call should use cache
    value = sm.get_secret("cached_key", SecretScope.USER)
    assert value == "cached_value"
    # Should not call provider again
    assert len(mock_provider.get_calls) == 1


def test_set_secret_with_provider_stores_and_caches(database_manager, mock_provider):
    """Test that set_secret stores in provider and caches."""
    sm = SecretManager(database_manager, provider=mock_provider)

    # Set secret
    result = sm.set_secret("new_key", "new_value", SecretScope.USER)
    assert result is True
    assert len(mock_provider.set_calls) == 1

    # Verify it's cached (no get call needed)
    value = sm.get_secret("new_key", SecretScope.USER)
    assert value == "new_value"
    assert len(mock_provider.get_calls) == 0  # Should not get, uses cache


def test_set_secret_without_provider_caches_only(database_manager):
    """Test that set_secret without provider only caches."""
    sm = SecretManager(database_manager, provider=None)

    # Set secret
    result = sm.set_secret("local_key", "local_value", SecretScope.USER)
    assert result is True

    # Verify it's cached
    value = sm.get_secret("local_key", SecretScope.USER)
    assert value == "local_value"


def test_scope_isolation_in_cache(database_manager):
    """Test that different scopes are properly isolated in cache."""
    sm = SecretManager(database_manager, provider=None)

    # Set same key in different scopes
    sm.set_secret("key", "user_value", SecretScope.USER)
    sm.set_secret("key", "project_value", SecretScope.PROJECT, project="proj1")

    # Verify isolation
    assert sm.get_secret("key", SecretScope.USER) == "user_value"
    assert sm.get_secret("key", SecretScope.PROJECT, project="proj1") == "project_value"


def test_project_isolation_in_cache(database_manager):
    """Test that different projects are properly isolated."""
    sm = SecretManager(database_manager, provider=None)

    # Set same key for different projects
    sm.set_secret("db_password", "pass1", SecretScope.PROJECT, project="project1")
    sm.set_secret("db_password", "pass2", SecretScope.PROJECT, project="project2")

    # Verify isolation
    assert (
        sm.get_secret("db_password", SecretScope.PROJECT, project="project1") == "pass1"
    )
    assert (
        sm.get_secret("db_password", SecretScope.PROJECT, project="project2") == "pass2"
    )


def test_env_fallback_for_user_scope(database_manager, monkeypatch):
    """Test that environment variables are used as fallback for USER scope."""
    sm = SecretManager(database_manager, provider=None)

    # Set environment variable
    monkeypatch.setenv("ENV_SECRET", "env_value")

    # Should fallback to env var
    value = sm.get_secret("ENV_SECRET", SecretScope.USER)
    assert value == "env_value"


def test_no_env_fallback_for_project_scope(database_manager, monkeypatch):
    """Test that environment variables are NOT used for PROJECT scope."""
    sm = SecretManager(database_manager, provider=None)

    # Set environment variable
    monkeypatch.setenv("PROJECT_SECRET", "env_value")

    # Should NOT fallback to env var for PROJECT scope
    value = sm.get_secret("PROJECT_SECRET", SecretScope.PROJECT, project="proj1")
    assert value is None


def test_clear_cache_removes_all_secrets(database_manager, mock_provider):
    """Test that clear_cache removes all cached secrets."""
    mock_provider.add_mock_secret("secret1", "value1", SecretScope.USER)
    mock_provider.add_mock_secret("secret2", "value2", SecretScope.USER)

    sm = SecretManager(database_manager, provider=mock_provider)

    # Get and cache secrets
    sm.get_secret("secret1", SecretScope.USER)
    sm.get_secret("secret2", SecretScope.USER)
    assert len(mock_provider.get_calls) == 2

    # Clear cache
    sm.clear_cache()

    # Next get should call provider again (not from cache)
    sm.get_secret("secret1", SecretScope.USER)
    assert len(mock_provider.get_calls) == 3  # One more call after clear


def test_nonexistent_secret_returns_none(database_manager, mock_provider):
    """Test that nonexistent secret returns None."""
    sm = SecretManager(database_manager, provider=mock_provider)

    value = sm.get_secret("nonexistent", SecretScope.USER)
    assert value is None


def test_cache_key_generation(database_manager):
    """Test that cache keys are generated correctly."""
    sm = SecretManager(database_manager, provider=None)

    # Same key, different scopes should be different
    sm.set_secret("key1", "value_user", SecretScope.USER)
    sm.set_secret("key1", "value_project", SecretScope.PROJECT, project="proj1")

    # Verify both are stored separately
    assert sm.get_secret("key1", SecretScope.USER) == "value_user"
    assert (
        sm.get_secret("key1", SecretScope.PROJECT, project="proj1") == "value_project"
    )


def test_persistence_across_manager_instances(database_manager):
    """Test that secrets persist across manager instances."""
    sm1 = SecretManager(database_manager, provider=None)
    sm1.set_secret("persistent_key", "persistent_value", SecretScope.USER)

    # Create new manager with same database
    sm2 = SecretManager(database_manager, provider=None)
    value = sm2.get_secret("persistent_key", SecretScope.USER)
    assert value == "persistent_value"


def test_provider_store_failure_returns_false(database_manager):
    """Test that provider set failure is handled properly."""

    class FailingProvider(SecretProvider):
        def get_secret(self, key, scope, project=None):
            return None

        def set_secret(self, secret):
            return False  # Simulate failure

    sm = SecretManager(database_manager, provider=FailingProvider())
    result = sm.set_secret("key", "value", SecretScope.USER)
    assert result is False
