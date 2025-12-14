# Usage Guide: Developing Plugins

This guide explains how to extend ArteCore by creating plugins. Plugins can provide new tools, define new agents, or add core functionality.

## Creating a Plugin

Plugins live in the `src/artreactor/plugins/` directory. Each plugin is a directory containing at least a `plugin.toml` manifest and a Python module (usually `plugin.py` or `__init__.py`).

### 1. Directory Structure

Create a new directory for your plugin:

```bash
mkdir src/artreactor/plugins/my_awesome_plugin
```

### 2. Plugin Manifest (`plugin.toml`)

Create a `plugin.toml` file to define your plugin's metadata:

```toml
name = "my-awesome-plugin"
version = "0.1.0"
description = "A plugin that does awesome things"
type = "core"  # or "agent", "router", "app"
priority = 100
```

### 3. Plugin Implementation (`plugin.py`)

Create a `plugin.py` file with your plugin class. It must inherit from `Plugin` (or a subclass like `AgentPlugin`).

```python
from artreactor.core.interfaces.plugin import Plugin, PluginManifest
from typing import Any
import logging

logger = logging.getLogger(__name__)

class MyAwesomePlugin(Plugin):
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)

    async def initialize(self):
        logger.info("MyAwesomePlugin initialized!")

    async def shutdown(self):
        logger.info("MyAwesomePlugin shutting down.")
```

## Adding a Tool

To expose a function as a tool for agents, use the `@tool` decorator within your plugin class.

```python
from artreactor.core.decorators import tool

class MyAwesomePlugin(Plugin):
    # ... init methods ...

    @tool(name="calculate_sum", description="Calculates the sum of two numbers")
    def calculate_sum(self, a: int, b: int) -> int:
        """
        Adds two numbers together.
        
        Args:
            a: First number
            b: Second number
        """
        return a + b
```

The `PluginManager` will automatically discover this method and register it as a tool named `calculate_sum`.

## Adding an Agent

To define a new type of agent, inherit from `AgentPlugin`.

```python
from artreactor.core.interfaces.agent_plugin import AgentPlugin
from typing import List

class MySpecialAgent(AgentPlugin):
    @property
    def agent_type(self) -> str:
        return "special_agent"

    @property
    def model_id(self) -> str:
        return "gemini-flash"

    @property
    def system_prompt(self) -> str:
        return "You are a special agent designed to handle specific tasks."

    @property
    def tool_names(self) -> List[str]:
        # List tools this agent should have access to
        return ["calculate_sum", "web_search"]
```

## Configuration

Plugins can be configured via the central `config.toml` (if implemented) or their own `plugin.toml`.

The `PluginManager` respects the following standard configuration in `plugin.toml`:

-   **enabled**: Set to `false` to disable the plugin.
-   **priority**: Higher numbers load first.
-   **timing**: Controls when the plugin loads (e.g., `startup`, `post_startup`).
