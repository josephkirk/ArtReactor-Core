# ArtReactor
[![Build & Test](https://github.com/josephkirk/ArtReactor-Core/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/josephkirk/ArtReactor-Core/actions/workflows/ci.yml)
[![Lint](https://github.com/josephkirk/ArtReactor-Core/ actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/josephkirk/ArtReactor-Core/actions/workflows/lint.yml)

## Purpose
ArtReactor Core aim to be the backbone framework for the modern Game Asset Pipeline, designed to be extensible and modular. Its primary goal is to allow developers to "write once and expose" functionality for other tools to use, enforced with strict security controls. It facilitates communication between different software and treats Agentic AI as a first-class citizen, enabling complex, cross-application workflows.

## Tech Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Agent Framework**: PydanticAI (formerly smolagents)
- **Server**: uvicorn
- **Package Manager**: uv
- **Build System**: hatchling
- **Key Libraries**:
    - `pydantic-ai` (AI agent framework with type safety)
    - `litellm` (LLM abstraction)
    - `pystray`, `pillow` (System tray integration)
    - `pyyaml`, `toml` (Configuration)
    - `aiofiles` (Async file I/O)

## Project Conventions

### Code Style
- **Python**: Follows standard Python conventions (PEP 8).
- **Imports**: Use absolute imports from the `artreactor` package (e.g., `from artreactor.core import ...`).
- **Async**: Heavy use of `async`/`await` for I/O bound operations, especially in API endpoints and plugin interactions.
- **Type Hinting**: Extensive use of type hints for clarity and IDE support.

### Architecture Patterns
- **Plugin Architecture**: Core functionality is extended via plugins (`CorePlugin`, `ToolPlugin`, `AgentPlugin`, `ModelPlugin`, `UIPlugin`).
- **Managers**: Centralized managers (`AgentManager`, `PluginManager`, `ModelManager`) handle lifecycle and registry of components.
- **Dependency Injection**: Services and managers are often passed or accessed via a central hub or context.
- **Src-Layout**: Source code is located in `src/artreactor`.

### Testing Strategy
- **Framework**: `pytest`
- **Async Testing**: `pytest-asyncio` for async tests.
- **Structure**:
    - `tests/unit`: Isolated tests for individual components.
    - `tests/integration`: Tests ensuring components (e.g., Agents and Tools) work together.
    - `tests/mocks`: Mock implementations (e.g., `MockModel`) to simulate external dependencies like LLMs.
- **Command**: `uv run pytest`

## Domain Context
- **Game Asset Pipeline**: The system is central to managing and automating the flow of game assets between various DCC (Digital Content Creation) tools and engines.
- **Agentic AI**: Agents are first-class citizens, capable of orchestrating complex pipelines and interacting with external tools securely.
- **Inter-Software Communication**: Facilitates data exchange and command execution between different software applications in the pipeline.
- **Security**: Strict access controls and permissions are enforced for all plugin and agent interactions.
- **MCP (Model Context Protocol)**: Support for exposing functionality via MCP.
- **Plugins**:
    - **Manifest**: Plugins are defined by a `plugin.toml`.
    - **Discovery**: See "Plugin Management" section.

## Important Constraints
- **Windows OS**: The primary development and deployment environment is Windows.
- **Local Focus**: Designed to run locally or as a self-hosted service.

## External Dependencies
- **LLM Providers**: Relies on external or local LLM providers (OpenAI, Anthropic, Ollama, etc.) via `litellm`.

## Desktop Application (ArcVision)
ArteCore includes a native desktop frontend **ArcVision** (located in `src/ArcVision`).
- **Framework**: Tauri v2
- **Function**: Wrapper/Manager for the Core Service.
- **Build**: Run `.\scripts\build.ps1` to build the full desktop application.

## Event System
The Event System allows decoupled communication between components.
- **Decorators**: `@event` to define events, `@on` to bind listeners.
- **Features**: Async support, Unbind (`off`), Fire-and-Forget listeners.
- **Performance**: Capable of handling 1M+ listeners and 100k+ events efficiently.

## CLI Usage (Arte)
ArtReactor Core provides a CLI tool `arte` for managing the service and plugins.

```bash
# Start the service
arte start

# List available plugin templates
arte plugin templates

# Create a new plugin in a host project
arte plugin create my-plugin --type core

# Initialize a standalone plugin repository
arte plugin init-project my-plugin --type core

# Install a plugin from git
arte plugin install https://github.com/user/plugin-repo.git

# Install a plugin from local path (copy mode)
arte plugin install /path/to/plugin

# Install a plugin in dev mode (symlink)
arte plugin install /path/to/plugin --link
```

## Plugin Management
Plugins are the core extensibility mechanism.
- **Manifest**: Plugins are defined by a `plugin.toml`.
- **Discovery**: Plugins are auto-discovered from:
    1. `./plugins` (Project root)
    2. `src/artreactor/plugins` (System plugins)
    3. Custom paths defined in `config.toml` under `plugin_dirs`.

### Creating Plugins

#### In a Host Project
Use `arte plugin create` to scaffold a new plugin in the current project:
```bash
arte plugin create my-plugin --type core
```
This creates `plugins/my-plugin/` with the necessary files.

#### As a Standalone Repository
Use `arte plugin init-project` to create a complete standalone plugin repository:
```bash
# Create a new directory or navigate to an existing repo
mkdir my-plugin && cd my-plugin

# Initialize the plugin project
arte plugin init-project my-plugin --type core
```

This creates a complete project structure:
```
my-plugin/
├── plugins/
│   └── my-plugin/         # Your plugin code
│       ├── plugin.toml
│       ├── __init__.py
│       └── SKILL.md
├── tests/
│   └── test_plugin_load.py  # Basic plugin loading test
├── pyproject.toml         # Dependencies (includes artreactor)
├── README.md              # Usage instructions
└── .gitignore
```

**Available Plugin Types**: `core`, `router`, `app`, `model`, `agent`, `ui`.

### Installing Plugins

#### From Git Repository
```bash
arte plugin install https://github.com/user/plugin-repo.git
```
Clones the repository into `./plugins/`.

#### From Local Path
```bash
# Copy mode (for deployment)
arte plugin install /path/to/plugin

# Dev mode with symlink (for development)
arte plugin install /path/to/plugin --link
```

**Plugin Repository Detection:**
- If the path contains `plugin.toml` at the root, it's treated as a plugin.
- If the path contains `plugins/<name>/plugin.toml`, the plugin is auto-detected.
- If multiple plugins are found, you'll be prompted to specify which one.

**Dev Mode (`--link`):**
- Creates a symlink instead of copying files.
- Allows editing the plugin in its original location.
- Changes are immediately reflected in the host project.
- Perfect for developing a plugin in its own repository.

### Plugin Development Workflow

#### Two-Repository Development Pattern
1. **Plugin Repository** (standalone):
   ```bash
   # Initialize plugin project
   mkdir my-awesome-plugin && cd my-awesome-plugin
   arte plugin init-project my-awesome-plugin --type core
   
   # Install dependencies
   pip install -e .
   
   # Run tests
   pytest
   ```

2. **Host Project** (uses the plugin):
   ```bash
   # Link the plugin for development
   arte plugin install ../my-awesome-plugin --link
   
   # Start the service
   arte start
   
   # When done developing, unlink and install normally
   rm -rf plugins/my-awesome-plugin
   arte plugin install ../my-awesome-plugin
   ```

This workflow allows you to:
- Develop and test the plugin independently
- Use version control on just the plugin
- Share the plugin as a separate package
- Iterate quickly with `--link` mode

## Agent Skills

Agent Skills is a powerful feature that allows plugins to expose their capabilities to AI agents through `SKILL.md` files. This enables agents to automatically discover and use plugin functionality based on context.

### What is a SKILL.md?

A `SKILL.md` file is a markdown document that describes what a plugin can do, when it should be used, and how to use it. It follows the [Anthropic Agent Skills format](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) with YAML frontmatter for metadata.

### Structure of SKILL.md

```markdown
---
name: Skill Name
description: Brief description of what this skill provides
---

## Context Keywords

- keyword1
- keyword2
- keyword3

## Tools

- `tool_name_1` - Description
- `tool_name_2` - Description

## Instructions

Detailed instructions on how to use this skill effectively.

## Examples

Concrete examples showing how to use the skill.
```

**Key Components:**
- **YAML Frontmatter**: Contains `name` and `description` metadata (required)
- **Context Keywords**: List of keywords for context-based skill discovery
- **Tools**: Available tools/functions that the skill provides
- **Instructions**: Step-by-step guide for using the skill
- **Examples**: Concrete usage examples with code snippets

### Creating Plugins with Skills

When you create a new plugin using `arte plugin create`, a SKILL.md template is automatically included. Simply fill in the sections with relevant information about your plugin's capabilities.

### How Agents Use Skills

1. **Discovery**: When a plugin loads, its SKILL.md is parsed and registered with the SkillManager
2. **Context Matching**: When an agent processes a request, it searches for skills whose keywords match the request context
3. **Contextual Injection**: Matching skills are automatically added to the agent's context, providing instructions and tool information
4. **Execution**: The agent can then use the described tools to complete the task

### Example

See `plugins/example-git-skill/SKILL.md` for a complete example of a well-documented skill.

## Configuration
The service is configured via `config.toml` in the project root.

### Structure
```toml
# Additional plugin search paths
plugin_dirs = ["./my_plugins", "C:/path/to/plugins"]

# Logging Configuration
[logging]
level = "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL
enabled = true
providers = ["console"]

# Plugin Configuration
[plugins.core-git]
enabled = true
priority = 100

[plugins.my-plugin]
enabled = false # Disable specific plugins
```

### Key Settings
- **`plugin_dirs`**: List of additional directories to scan for plugins.
- **`[plugins.<name>]`**: Configure specific plugins. `enabled` and `priority` are supported by default.
- **`[logging]`**: Configure global logging levels and providers.
