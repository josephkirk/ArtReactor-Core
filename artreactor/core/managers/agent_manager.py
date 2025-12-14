from pydantic_ai import Agent
from typing import List, Optional, Dict, Any, Callable
import inspect
import logging
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    """Structured tool definition using Pydantic"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    func: Callable[..., Any]
    parameters: Optional[Dict[str, Any]] = None

    @property
    def inputs(self) -> Dict[str, Any]:
        """Alias for parameters for backward compatibility"""
        return self.parameters or {}


class AgentManager:
    """
    Manages PydanticAI agents and tools with proper async support.

    Key architectural advantages leveraged:
    - Native async/await support (no more sync wrappers)
    - Pydantic models for structured inputs/outputs
    - Dependency injection for context passing
    - Type-safe tool definitions
    """

    def __init__(self, secret_manager=None, model_manager=None, skill_manager=None):
        self.secret_manager = secret_manager
        self.model_manager = model_manager
        self.skill_manager = skill_manager
        self.tools: List[ToolDefinition] = []
        self.agents: Dict[str, Agent] = {}
        self.agent: Optional[Agent] = None
        import asyncio

        self.lock = asyncio.Lock()
        self._init_agent()

    async def register_tool(self, tool_def: ToolDefinition, reinit_agent: bool = True):
        """Register a tool definition for use by agents (async, thread-safe)

        Args:
            tool_def (ToolDefinition): The tool to register.
            reinit_agent (bool): Whether to reinitialize the agent after registration. Defaults to True.
        """
        async with self.lock:
            self.tools.append(tool_def)
            # Reinitialize agent with new tools if requested
            if self.agent and reinit_agent:
                self._init_agent()

    async def register_tools(self, tool_defs: List[ToolDefinition]):
        """Register multiple tool definitions at once and reinitialize agent only once."""
        async with self.lock:
            self.tools.extend(tool_defs)
            if self.agent:
                self._init_agent()

    def _create_tool_wrapper(self, tool_def: ToolDefinition) -> Callable:
        """
        Create a tool wrapper that works with PydanticAI's Tool system.
        PydanticAI automatically handles async functions.
        """
        func = tool_def.func

        # If the function is async, return it as-is for PydanticAI
        # PydanticAI natively supports async tools
        if inspect.iscoroutinefunction(func):
            return func

        # For sync functions, create an async wrapper
        async def async_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return async_wrapper

    def _init_agent(self):
        """Initialize the default agent with configured model"""
        if not self.secret_manager:
            return

        api_key = self.secret_manager.get_secret("GEMINI_API_KEY")
        if not api_key:
            return

        try:
            # API keys should be set via environment variables externally.
            # Ensure GEMINI_API_KEY is set before starting the process.
            import os

            if "GEMINI_API_KEY" not in os.environ:
                # Only set if not already present (backward compatibility)
                os.environ["GEMINI_API_KEY"] = api_key
                logger.warning(
                    "GEMINI_API_KEY set programmatically. Consider setting it externally before process start."
                )

            model_name = os.environ.get(
                "GEMINI_MODEL_NAME", "gemini:gemini-2.0-flash-exp"
            )

            # Create agent
            # PydanticAI Agent handles tools via decorator or method calls
            self.agent = Agent(
                model_name,
                system_prompt="You are a helpful assistant for game asset pipeline tasks.",
            )

            # Register tools with the agent
            self._register_tools_with_agent(self.agent)

            logger.info("Agent initialized with Gemini model via PydanticAI.")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")

    def _register_tools_with_agent(self, agent: Agent):
        """Helper method to register all tools with an agent instance."""
        for tool_def in self.tools:
            tool_func = self._create_tool_wrapper(tool_def)
            agent.tool_plain(
                tool_func, name=tool_def.name, description=tool_def.description
            )

    async def run_agent(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Run agent with proper async support and dependency injection.

        PydanticAI advantages:
        - Native async/await (no sync wrappers)
        - Context passed via deps parameter
        - Structured responses via Pydantic models
        """
        async with self.lock:
            if not self.agent:
                # Try to init again in case secret was added later
                self._init_agent()

            if not self.agent:
                # Fallback for testing without API key
                if context and "mock" in prompt.lower():
                    return f"Mock response: {prompt}. Context: {context}"
                return f"Agent received: {prompt}. Context: {context}. (Agent not configured - Missing GEMINI_API_KEY)"

            # Build full prompt with context and skills
            full_prompt = ""

            # Add skill context if available
            if self.skill_manager:
                skill_context = self.skill_manager.get_context_for_agent(prompt)
                if skill_context:
                    full_prompt += f"{skill_context}\n\n"

            # Add user context
            if context:
                full_prompt += f"Context: {context}\n\n"

            # Add the actual prompt
            full_prompt += prompt

            # PydanticAI's run method is async and accepts deps for dependency injection
            result = await self.agent.run(full_prompt, deps=context or {})

            # PydanticAI returns AgentRunResult object with output attribute
            # Convert to string for compatibility
            return str(result.output)

    async def register_plugin_tools(self, plugin_manager):
        """Register tools from all loaded plugins"""
        for plugin in plugin_manager.plugins.values():
            if hasattr(plugin, "tools"):
                for tool_def in plugin.tools:
                    # Convert plugin tool definition to ToolDefinition
                    pydantic_tool = ToolDefinition(
                        name=tool_def.name,
                        description=tool_def.description,
                        func=tool_def.func,
                    )
                    await self.register_tool(pydantic_tool)
                    logger.info(f"Registered plugin tool: {pydantic_tool.name}")

    async def load_project_tools(self, project_name: str, project_manager):
        """Load tools from project workflows"""
        workflows = project_manager.get_workflows(project_name)
        for wf in workflows:
            import importlib.util

            path = wf["path"]
            name = wf["name"]

            spec = importlib.util.spec_from_file_location(name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    func = getattr(module, name)

                    description = inspect.getdoc(func) or wf.get(
                        "description", f"Tool {name}"
                    )
                    tool = ToolDefinition(
                        name=f"{project_name}_{name}",
                        description=description,
                        func=func,
                    )
                    await self.register_tool(tool)
                    logger.info(f"Registered project tool: {tool.name}")
                except Exception as e:
                    logger.error(f"Failed to load project tool {name}: {e}")

    async def register_agent_plugin(self, plugin: Any):
        """
        Register an AgentPlugin and create a PydanticAI agent.

        PydanticAI advantages:
        - Structured agent configuration
        - Type-safe tool registration
        - Better dependency management
        """
        if not self.model_manager:
            logger.error("ModelManager required to register agents")
            return

        model = self.model_manager.get_model(plugin.model_id)
        if not model:
            logger.error(
                f"Model {plugin.model_id} not found for agent {plugin.agent_type}"
            )
            return

        # Resolve tools
        tool_map = {t.name: t for t in self.tools}
        agent_tools = []
        for tool_name in plugin.tool_names:
            if tool_name in tool_map:
                agent_tools.append(tool_map[tool_name])
            else:
                logger.warning(
                    f"Tool {tool_name} not found for agent {plugin.agent_type}"
                )

        # Create PydanticAI agent
        try:
            agent = Agent(
                model,
                system_prompt=getattr(plugin, "system_prompt", None)
                or "You are a helpful assistant.",
            )

            # Register tools with this agent
            for tool_def in agent_tools:
                tool_func = self._create_tool_wrapper(tool_def)
                agent.tool_plain(
                    tool_func, name=tool_def.name, description=tool_def.description
                )

            # Handle managed agents (agents that can call other agents)
            for agent_name in plugin.managed_agents:
                managed = self.get_agent(agent_name)
                if managed:
                    # Create a tool that delegates to the managed agent
                    # Use a factory function to create proper closure for each agent
                    def make_delegator(managed_agent):
                        async def call_managed_agent(prompt: str) -> str:
                            result = await managed_agent.run(prompt)
                            return str(result.output)

                        return call_managed_agent

                    agent.tool_plain(
                        make_delegator(managed),
                        name=agent_name,
                        description=f"Delegate to {agent_name} agent",
                    )

            self.agents[plugin.agent_type] = agent
            logger.info(f"Registered agent: {plugin.agent_type}")
        except Exception as e:
            logger.error(f"Failed to create agent {plugin.agent_type}: {e}")

    def get_agent(self, agent_type: str) -> Optional[Agent]:
        """Get a registered agent by type"""
        return self.agents.get(agent_type)
