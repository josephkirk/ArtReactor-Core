# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Agent Framework Migration**: Refactored from smolagents to PydanticAI
    - **Native async/await**: Removed all sync wrappers for proper async support throughout
    - **Type safety**: Full typing with Pydantic models via `ToolDefinition`
    - **Dependency injection**: Clean context passing via `deps` parameter
    - **Better tool registration**: Programmatic registration with `tool_plain` method
    - **Structured responses**: `AgentRunResult` with typed `output` attribute
    - **Proper credential management**: API keys via environment variables
    - **Updated interfaces**: `ModelPlugin` now returns PydanticAI `Model` interface
    - **Test infrastructure**: New `MockPydanticModel` for testing
    - **Documentation**: Updated README and project docs to reflect new framework

### Fixed
- Fixed closure issue in managed agent delegation loops
- Removed unused imports in tool utilities
- Corrected model configuration to use environment variables for API keys

## [2025-12-07-event-system]

### Added
- **Event System**: robust, decoupled event system for component communication.
    - `EventManager`: Central singleton for managing events.
    - `@event` decorator: Mark functions as event emitters (emits return value).
    - `@on` decorator: Register listeners (supports async and sync).
    - `off` function: Unbind listeners.
    - **Fire-and-Forget**: Support for non-blocking background listeners via `fire_and_forget=True`.
    - **Performance**: Optimized for high load (verified 1M listeners, 100k events).
    - Automatic threading for synchronous listeners to prevent event loop blocking.
