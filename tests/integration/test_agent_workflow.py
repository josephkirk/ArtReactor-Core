import pytest
from artreactor.core.managers.agent_manager import AgentManager
from artreactor.core.managers.model_manager import ModelManager
from artreactor.core.interfaces.agent_plugin import AgentPlugin
from artreactor.core.interfaces.model_plugin import ModelPlugin
from artreactor.core.interfaces.plugin import PluginManifest, PluginType


class MockAgentPlugin(AgentPlugin):
    def __init__(self):
        manifest = PluginManifest(
            name="mock-agent", version="0.1", type=PluginType.AGENT
        )
        super().__init__(manifest, None)

    @property
    def agent_type(self):
        return "mock-agent"

    @property
    def model_id(self):
        return "mock-model"

    @property
    def system_prompt(self):
        return "You are a mock agent."

    async def initialize(self):
        pass

    async def shutdown(self):
        pass


class MockModelPlugin(ModelPlugin):
    def __init__(self):
        manifest = PluginManifest(
            name="mock-model-plugin", version="0.1", type=PluginType.MODEL
        )
        super().__init__(manifest, None)

    @property
    def model_id(self):
        return "mock-model"

    @property
    def backend(self):
        return "test"

    def get_model(self):
        # Return 'test' for PydanticAI's test mode
        return "test"

    async def initialize(self):
        pass

    async def shutdown(self):
        pass


@pytest.mark.asyncio
async def test_agent_registration():
    model_manager = ModelManager()
    await model_manager.register_plugin(MockModelPlugin())

    agent_manager = AgentManager(model_manager=model_manager)

    plugin = MockAgentPlugin()
    await agent_manager.register_agent_plugin(plugin)

    # Assuming get_agent returns the agent instance
    assert agent_manager.get_agent("mock-agent") is not None


@pytest.mark.asyncio
async def test_agent_orchestration():
    model_manager = ModelManager()
    await model_manager.register_plugin(MockModelPlugin())

    agent_manager = AgentManager(model_manager=model_manager)

    # Register worker agent
    class WorkerAgentPlugin(MockAgentPlugin):
        @property
        def agent_type(self):
            return "worker_agent"

    worker_plugin = WorkerAgentPlugin()
    await agent_manager.register_agent_plugin(worker_plugin)

    # Register manager agent that uses worker
    class ManagerAgentPlugin(AgentPlugin):
        def __init__(self):
            manifest = PluginManifest(
                name="manager", version="0.1", type=PluginType.AGENT
            )
            super().__init__(manifest, None)

        @property
        def agent_type(self):
            return "manager_agent"

        @property
        def model_id(self):
            return "mock-model"

        @property
        def system_prompt(self):
            return "You manage the worker."

        @property
        def managed_agents(self):
            return ["worker_agent"]

        async def initialize(self):
            pass

        async def shutdown(self):
            pass

    await agent_manager.register_agent_plugin(ManagerAgentPlugin())

    manager_agent = agent_manager.get_agent("manager_agent")
    assert manager_agent is not None

    # Verify both agents are registered
    worker_agent = agent_manager.get_agent("worker_agent")
    assert worker_agent is not None

    # The managed agents are registered as tools internally by PydanticAI
    # We can't directly access them, but we can verify the agents exist
    assert len(agent_manager.agents) == 2


def test_agent_config_export():
    class ConfigAgentPlugin(AgentPlugin):
        def __init__(self):
            manifest = PluginManifest(
                name="config-agent", version="0.1", type=PluginType.AGENT
            )
            super().__init__(manifest, None)

        @property
        def agent_type(self):
            return "config_agent"

        @property
        def model_id(self):
            return "config-model"

        @property
        def system_prompt(self):
            return "Config prompt"

        @property
        def tool_names(self):
            return ["tool1"]

        @property
        def managed_agents(self):
            return ["sub_agent"]

        @property
        def knowledge_config(self):
            return {"source": "docs"}

        async def initialize(self):
            pass

        async def shutdown(self):
            pass

    plugin = ConfigAgentPlugin()
    config = plugin.to_dict()

    assert config["type"] == "config_agent"
    assert config["model"] == "config-model"
    assert config["prompt"] == "Config prompt"
    assert config["tools"] == ["tool1"]
    assert config["managed_agents"] == ["sub_agent"]
    assert config["knowledge"] == {"source": "docs"}
