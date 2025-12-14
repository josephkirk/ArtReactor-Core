from abc import abstractmethod
from typing import List, Optional, Dict, Any
from artreactor.core.interfaces.plugin import Plugin


class AgentPlugin(Plugin):
    """
    Plugin for defining a new agent type.
    """

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Unique identifier for the agent type."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """ID of the model to use (must match a registered ModelPlugin)."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System instructions for the agent."""
        pass

    @property
    def tool_names(self) -> List[str]:
        """List of tool names this agent can use."""
        return []

    @property
    def managed_agents(self) -> List[str]:
        """List of other agent names this agent can manage."""
        return []

    @property
    def knowledge_config(self) -> Optional[Dict[str, Any]]:
        """Configuration for knowledge retrieval."""
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.agent_type,
            "model": self.model_id,
            "prompt": self.system_prompt,
            "tools": self.tool_names,
            "managed_agents": self.managed_agents,
            "knowledge": self.knowledge_config,
        }
