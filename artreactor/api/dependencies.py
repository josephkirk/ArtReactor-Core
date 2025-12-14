from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.core.managers.secret_manager import SecretManager
from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)
from artreactor.core.managers.agent_manager import AgentManager
from artreactor.core.managers.skill_manager import SkillManager

# Initialize Managers
skill_manager = SkillManager()
plugin_manager = PluginManager(skill_manager=skill_manager)
database_provider = SqliteDatabaseProvider()
database_manager = DatabaseManager(database_provider)
# Secret manager now uses database for caching, no provider means local-only mode
secret_manager = SecretManager(database_manager, provider=None)
# Project manager now uses database for caching, no provider means local-only mode
project_manager = ProjectManager(database_manager, provider=None)
agent_manager = AgentManager(secret_manager, skill_manager=skill_manager)


def get_plugin_manager():
    return plugin_manager


def get_project_manager():
    return project_manager


def get_secret_manager():
    return secret_manager


def get_agent_manager():
    return agent_manager


def get_skill_manager():
    return skill_manager


def get_database_manager():
    return database_manager
