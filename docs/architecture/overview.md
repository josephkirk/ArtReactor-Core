# Architecture Overview

ArtReactor Core is built on a modular, plugin-based architecture designed for extensibility, security, and performance in game asset pipeline workflows.

## Design Philosophy

### 1. Modularity First

Every feature is implemented as a plugin. The core provides only:

- Plugin discovery and lifecycle management
- Event system for decoupled communication
- Agent orchestration and tool registry
- HTTP API foundation

This ensures that features can be added, removed, or replaced without touching core code.

### 2. AI as a First-Class Citizen

Agents are not an afterthought—they're central to the architecture:

- Tools are automatically discovered and exposed to agents
- Agent Skills provide contextual documentation
- Natural language interfaces are prioritized
- Tool calling is type-safe and validated

### 3. Security by Design

Every operation goes through permission checks:

- Plugins declare required permissions
- File operations are sandboxed
- API keys are never logged
- Cross-origin requests are controlled

### 4. Performance Matters

Game pipelines process large assets:

- Async I/O throughout
- Event system handles 100k+ events efficiently
- Lazy loading of plugins
- Optimized for batch operations

## High-Level Architecture

```mermaid
graph TB
    subgraph "External Layer"
        DCC[DCC Tools<br/>Maya, Blender, PS]
        Engine[Game Engines<br/>Unreal, Unity]
        AI[AI Agents<br/>Autonomous Tasks]
    end
    
    subgraph "API Layer"
        REST[REST API<br/>FastAPI]
        MCP[MCP Protocol<br/>Model Context]
    end
    
    subgraph "Core Layer"
        AM[Agent Manager]
        PM[Plugin Manager]
        EM[Event Manager]
        MM[Model Manager]
    end
    
    subgraph "Plugin Layer"
        CP[Core Plugins]
        RP[Router Plugins]
        AP[App Plugins]
        UP[UI Plugins]
    end
    
    subgraph "Infrastructure"
        LS[Logging System]
        TS[Telemetry System]
        FS[File System]
        DB[Database]
    end
    
    DCC --> REST
    Engine --> REST
    AI --> MCP
    
    REST --> AM
    MCP --> AM
    
    AM --> PM
    AM --> MM
    AM --> EM
    
    PM --> CP
    PM --> RP
    PM --> AP
    PM --> UP
    
    CP --> FS
    CP --> DB
    AM --> LS
    AM --> TS
    
    style AM fill:#4051b5
    style PM fill:#4051b5
```

## Core Principles

### Single Responsibility

Each component has one clear purpose:

- **AgentManager**: Orchestrates AI agents and tool execution
- **PluginManager**: Discovers, loads, and manages plugins
- **EventManager**: Routes events between components
- **ModelManager**: Manages AI model connections

### Dependency Inversion

Components depend on interfaces, not implementations:

```python
# Core depends on interface
class AgentManager:
    def register_tool(self, tool: Tool):
        pass

# Plugin implements interface
class MyPlugin(CorePlugin):
    @tool(name="my_tool")
    def my_tool(self):
        pass  # AgentManager doesn't know about MyPlugin
```

### Event-Driven Communication

Components communicate through events, not direct calls:

```python
# Plugin A fires an event
fire("asset.exported", {"path": "/path/to/asset.fbx"})

# Plugin B listens independently
@on("asset.exported")
async def handle_export(data):
    # Process the export
    pass
```

## Request Flow

### Agent Request Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant AgentManager
    participant Agent
    participant Tool
    participant Plugin
    
    User->>API: POST /api/agent/run
    API->>AgentManager: run_agent(prompt)
    AgentManager->>Agent: execute(prompt, tools)
    Agent->>Agent: Generate tool calls
    Agent->>Tool: call("export_mesh", {...})
    Tool->>Plugin: execute()
    Plugin-->>Tool: result
    Tool-->>Agent: result
    Agent->>Agent: Generate response
    Agent-->>AgentManager: response
    AgentManager-->>API: response
    API-->>User: JSON response
```

### Plugin Loading Flow

```mermaid
sequenceDiagram
    participant System
    participant PM as PluginManager
    participant Plugin
    participant AM as AgentManager
    
    System->>PM: initialize()
    PM->>PM: scan_directories()
    PM->>PM: parse_manifests()
    PM->>PM: sort_by_priority()
    
    loop For each plugin
        PM->>Plugin: __init__(manifest, context)
        PM->>Plugin: initialize()
        Plugin-->>PM: initialized
        
        PM->>Plugin: discover_tools()
        Plugin-->>PM: tool_list
        
        PM->>AM: register_tools(tool_list)
    end
    
    PM-->>System: all_plugins_loaded
```

## Component Interactions

### Tool Registration

```mermaid
graph LR
    A[Plugin defines @tool] --> B[PluginManager discovers]
    B --> C[Wrapped as ServiceTool]
    C --> D[Registered with AgentManager]
    D --> E[Available to Agents]
    
    style D fill:#4051b5
```

### Event Propagation

```mermaid
graph LR
    A[fire event] --> B[EventManager]
    B --> C[Find listeners]
    C --> D[Listener 1]
    C --> E[Listener 2]
    C --> F[Listener 3]
    
    style B fill:#4051b5
```

## Key Architectural Decisions

### Why Plugins Over Extensions?

**Decision**: Use a plugin architecture rather than simple extensions.

**Rationale**:
- Plugins can be disabled without code changes
- Clear boundaries and ownership
- Independent testing and versioning
- Security isolation

### Why FastAPI?

**Decision**: Use FastAPI as the HTTP framework.

**Rationale**:
- Async support is native
- Automatic API documentation (OpenAPI)
- Type validation with Pydantic
- High performance
- Modern Python patterns

### Why Event System Over Direct Coupling?

**Decision**: Use events for inter-plugin communication.

**Rationale**:
- Plugins don't need to know about each other
- Features can be added/removed without breaking others
- Easier testing (mock event listeners)
- Natural audit trail

### Why PydanticAI?

**Decision**: Use PydanticAI for agent framework.

**Rationale**:
- Type-safe tool definitions
- Multiple LLM provider support
- Structured outputs with validation
- Async-first design
- Pythonic API

## Scalability Considerations

### Horizontal Scaling

ArtReactor can run multiple instances:

- Stateless design (except for local file operations)
- Shared configuration via file or network storage
- Load balancer in front for distribution

### Plugin Isolation

Plugins run in the same process but are isolated:

- Separate namespaces
- Permission boundaries
- Resource limits (future)

### Performance Optimization

- **Lazy Loading**: Plugins load only when needed
- **Async I/O**: Non-blocking file and network operations
- **Caching**: Frequently used data is cached
- **Batch Processing**: Support for processing multiple items

## Security Architecture

```mermaid
graph TD
    Request[Incoming Request] --> Auth[Authentication]
    Auth --> Perm[Permission Check]
    Perm --> Plugin[Plugin Execution]
    Plugin --> Sandbox[Sandboxed Operations]
    Sandbox --> Audit[Audit Log]
    
    style Auth fill:#d32f2f
    style Perm fill:#d32f2f
    style Sandbox fill:#d32f2f
```

### Defense in Depth

1. **API Layer**: Authentication and rate limiting
2. **Manager Layer**: Permission validation
3. **Plugin Layer**: Sandboxed file/network access
4. **Audit Layer**: All operations logged

## Next Steps

Explore specific components:

- [Core Components](core-components.md) - Detailed manager documentation
- [Plugin System](plugin-system.md) - How plugins work
- [Event System](event-system.md) - Event-driven architecture
- [Data Flow](data-flow.md) - How data moves through the system
