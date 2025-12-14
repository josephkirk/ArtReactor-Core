import pytest
from artreactor.core.managers.model_manager import ModelManager
from artreactor.core.interfaces.model_plugin import ModelPlugin
from artreactor.core.interfaces.plugin import PluginManifest, PluginType


class MockModelPlugin(ModelPlugin):
    def __init__(self):
        manifest = PluginManifest(
            name="mock-plugin", version="0.1.0", type=PluginType.MODEL
        )
        super().__init__(manifest, None)

    @property
    def model_id(self):
        return "mock-model"

    @property
    def backend(self):
        return "mock"

    def get_model(self):
        return "mock_model_instance"

    async def initialize(self):
        pass

    async def shutdown(self):
        pass


@pytest.mark.asyncio
async def test_model_manager_registration():
    manager = ModelManager()
    plugin = MockModelPlugin()
    await manager.register_plugin(plugin)

    assert manager.get_model("mock-model") == "mock_model_instance"
    assert manager.list_models() == {"mock-model": "mock"}


@pytest.mark.asyncio
async def test_transformers_model_loading():
    # PydanticAI doesn't use TransformersModel directly
    # It uses model identifiers like "openai:gpt-4" or custom models
    # For testing, we'll use a mock model

    class MockPydanticModelPlugin(ModelPlugin):
        def __init__(self):
            manifest = PluginManifest(
                name="tf-plugin", version="0.1", type=PluginType.MODEL
            )
            super().__init__(manifest, None)

        @property
        def model_id(self):
            return "tf-model"

        @property
        def backend(self):
            return "test"  # PydanticAI's test backend

        def get_model(self):
            # Return a model identifier for PydanticAI
            return "test"

        async def initialize(self):
            pass

        async def shutdown(self):
            pass

    manager = ModelManager()
    await manager.register_plugin(MockPydanticModelPlugin())

    assert manager.get_model("tf-model") is not None


@pytest.mark.asyncio
async def test_litellm_model_loading():
    # PydanticAI supports multiple providers via model identifiers
    # Format: "provider:model-name" or just "model-name" for supported providers

    class OpenAIPlugin(ModelPlugin):
        def __init__(self):
            manifest = PluginManifest(
                name="openai-plugin", version="0.1", type=PluginType.MODEL
            )
            super().__init__(manifest, None)

        @property
        def model_id(self):
            return "openai-gpt4"

        @property
        def backend(self):
            return "openai"

        def get_model(self):
            # PydanticAI uses model identifiers
            return "openai:gpt-4"

        async def initialize(self):
            pass

        async def shutdown(self):
            pass

    manager = ModelManager()
    await manager.register_plugin(OpenAIPlugin())

    assert manager.get_model("openai-gpt4") is not None
    assert manager.get_model("openai-gpt4") == "openai:gpt-4"
