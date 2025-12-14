# Logging and Telemetry

For detailed information, see [logging-and-telemetry.md](../logging-and-telemetry.md) in the docs root.

## Quick Start

Configure logging in `config.toml`:

```toml
[logging]
level = "INFO"
providers = ["console", "file"]
```

## Plugin Logging

```python
class MyPlugin(CorePlugin):
    async def initialize(self):
        self.logger.info("Plugin initialized")
        self.logger.debug("Debug information")
        self.logger.error("Error occurred")
```
