from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)
from artreactor.core.managers.secret_manager import (
    SecretManager,
    SecretScope,
)


def test_plugin_manager_init():
    pm = PluginManager()
    assert pm.plugins == {}


def test_project_manager_init(tmp_path):
    db_path = tmp_path / "test_db.db"
    db_provider = SqliteDatabaseProvider(str(db_path))
    db_manager = DatabaseManager(db_provider)
    pm = ProjectManager(db_manager, provider=None)
    assert pm.db == db_manager
    assert pm.provider is None


def test_secret_manager_init(tmp_path):
    db_path = tmp_path / "secrets.db"
    db_provider = SqliteDatabaseProvider(str(db_path))
    db_manager = DatabaseManager(db_provider)
    sm = SecretManager(db_manager, provider=None)

    sm.set_secret("test_key", "test_val", SecretScope.USER)
    assert sm.get_secret("test_key", SecretScope.USER) == "test_val"
    assert sm.get_secret("test_key", SecretScope.PROJECT) is None
