import pytest
import os
from artreactor.core.managers.secret_manager import (
    SecretManager,
    SecretScope,
)
from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)


@pytest.fixture
def database_manager(tmp_path):
    db_path = tmp_path / "test_secrets.db"
    provider = SqliteDatabaseProvider(str(db_path))
    return DatabaseManager(provider)


@pytest.fixture
def secret_manager(database_manager):
    return SecretManager(database_manager, provider=None)


def test_set_get_secret(secret_manager):
    secret_manager.set_secret("TEST_KEY", "test_value", SecretScope.USER)
    val = secret_manager.get_secret("TEST_KEY", SecretScope.USER)
    assert val == "test_value"


def test_get_secret_env_fallback(secret_manager):
    os.environ["ENV_TEST_KEY"] = "env_value"
    val = secret_manager.get_secret("ENV_TEST_KEY", SecretScope.USER)
    assert val == "env_value"
    del os.environ["ENV_TEST_KEY"]


def test_secret_scope_isolation(secret_manager):
    secret_manager.set_secret("KEY", "user_val", SecretScope.USER)
    secret_manager.set_secret("KEY", "proj_val", SecretScope.PROJECT, project="proj1")

    assert secret_manager.get_secret("KEY", SecretScope.USER) == "user_val"
    assert (
        secret_manager.get_secret("KEY", SecretScope.PROJECT, project="proj1")
        == "proj_val"
    )


def test_manager_persistence(tmp_path):
    db_path = tmp_path / "secrets.db"
    db_provider = SqliteDatabaseProvider(str(db_path))
    db_manager = DatabaseManager(db_provider)

    manager1 = SecretManager(db_manager, provider=None)
    manager1.set_secret("K", "V", SecretScope.USER)

    # Create new manager with same database
    manager2 = SecretManager(db_manager, provider=None)
    value = manager2.get_secret("K", SecretScope.USER)
    assert value == "V"
