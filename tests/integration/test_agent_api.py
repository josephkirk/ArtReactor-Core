from fastapi.testclient import TestClient
from artreactor.app import app
from artreactor.api.dependencies import get_agent_manager
from artreactor.core.managers.agent_manager import AgentManager
from pydantic_ai import Agent
from ..mocks.mock_llm import MockPydanticModel

client = TestClient(app)


def test_chat_endpoint():
    # Setup Mock AgentManager
    mock_am = AgentManager()
    mock_responses = ["Hello from Mock Agent"]  # Simpler PydanticAI response
    mock_model = MockPydanticModel(mock_responses)
    mock_am.agent = Agent(mock_model)

    # Override dependency
    app.dependency_overrides[get_agent_manager] = lambda: mock_am

    response = client.post(
        "/agent/chat", json={"prompt": "Hello", "context": {"user": "test"}}
    )

    # Clear override
    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "Hello from Mock Agent"
