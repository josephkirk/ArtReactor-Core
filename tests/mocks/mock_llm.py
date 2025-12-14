from typing import Any, List
from pydantic_ai.models import Model
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart


class MockPydanticModel(Model):
    """
    Mock model for testing PydanticAI agents.

    PydanticAI advantages for testing:
    - Structured responses via Pydantic models
    - Better type safety
    - Easier mocking of different scenarios
    """

    def __init__(self, responses: List[str]):
        """
        Initialize mock model with predetermined responses.

        Args:
            responses: List of response strings to return in sequence
        """
        self.responses = responses
        self.call_count = 0

    def model_name(self) -> str:
        """Return model name - required by PydanticAI"""
        return "mock-model"

    async def system(self) -> str:
        """Return system message - required by PydanticAI"""
        return "You are a helpful AI assistant."

    async def agent_model(
        self,
        *,
        function_tools: list[Any],
        allow_text_result: bool,
        result_tools: list[Any],
    ) -> Any:
        """
        Return agent-specific model wrapper for PydanticAI.

        This method is called by PydanticAI to get a model instance configured
        for a specific agent with its tools and settings. For testing purposes,
        we return self as the mock model handles all necessary functionality.
        """
        return self

    async def request(
        self, messages: List[ModelMessage], model_settings: Any = None, *args, **kwargs
    ) -> ModelResponse:
        """
        Handle model request with mock response.

        PydanticAI advantages:
        - Structured message format
        - Type-safe responses
        - Better async support
        """
        if self.call_count < len(self.responses):
            content = self.responses[self.call_count]
            self.call_count += 1
        else:
            content = "No more mock responses"

        # Return structured response with proper timestamp
        from datetime import datetime, timezone

        return ModelResponse(
            parts=[TextPart(content=content)],
            timestamp=datetime.now(timezone.utc),
        )
