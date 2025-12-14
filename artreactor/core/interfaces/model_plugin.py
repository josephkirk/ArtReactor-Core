from abc import abstractmethod
from typing import Union
from artreactor.core.interfaces.plugin import Plugin
from pydantic_ai.models import Model


class ModelPlugin(Plugin):
    """
    Plugin for registering a new model backend with PydanticAI.

    PydanticAI advantages:
    - Type-safe model interface
    - Better provider abstraction
    - Native async support
    - Structured model configuration
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique identifier for the model."""
        pass

    @property
    @abstractmethod
    def backend(self) -> str:
        """
        Backend type. PydanticAI supports:
        - 'openai' (GPT models)
        - 'anthropic' (Claude models)
        - 'gemini' (Google models)
        - 'groq' (Groq models)
        - 'ollama' (Local models)
        - 'test' (Mock/test models)
        """
        pass

    @abstractmethod
    def get_model(self) -> Union[Model, str]:
        """
        Returns the instantiated PydanticAI Model object or a model identifier string.

        Can return either:
        - A Model instance (for custom model implementations)
        - A model identifier string (e.g., "openai:gpt-4", "test") for PydanticAI to resolve

        PydanticAI Model interface provides:
        - Consistent API across providers
        - Native async support
        - Structured message handling
        - Tool calling support
        """
        pass
