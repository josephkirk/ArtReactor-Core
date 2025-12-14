# Configuration

ArtReactor uses TOML configuration files for customizing behavior.

## Configuration File Location

By default, ArtReactor looks for `config.toml` in:

1. Current working directory
2. Path specified by `ARTE_CONFIG_PATH` environment variable

Example:
```bash
export ARTE_CONFIG_PATH=/path/to/my-config.toml
arte start
```

## Configuration Structure

### Basic Configuration

```toml
# Global settings
debug = false

# Additional plugin search paths
plugin_dirs = ["./plugins", "./custom-plugins"]

# Logging Configuration
[logging]
level = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
enabled = true
providers = ["console", "file"]

[logging.file]
path = "logs/artreactor.log"
max_bytes = 10485760  # 10MB
backup_count = 5
```

### Plugin Configuration

Configure individual plugins:

```toml
[plugins.my-plugin]
enabled = true
priority = 100

# Plugin-specific settings
[plugins.my-plugin.settings]
api_key = "your-api-key"
timeout = 30
```

### Model Configuration

Configure AI models for agents:

```toml
[models]
default_provider = "openai"

[models.openai]
api_key = "sk-..."
model = "gpt-4"
temperature = 0.7

[models.anthropic]
api_key = "sk-ant-..."
model = "claude-3-sonnet"
```

### Server Configuration

```toml
[server]
host = "127.0.0.1"
port = 8000
workers = 4
reload = false
```

## Environment Variables

ArtReactor supports these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ARTE_CONFIG_PATH` | Path to config file | `config.toml` |
| `ARTE_PLUGIN_DIRS` | Additional plugin directories | - |
| `ARTE_LOG_LEVEL` | Override logging level | `INFO` |
| `ARTE_DEBUG` | Enable debug mode | `false` |

## Plugin Discovery

Plugins are discovered from multiple locations in this order:

1. **System Plugins**: `artreactor/plugins/` (built-in)
2. **Project Plugins**: `./plugins/` (current directory)
3. **Custom Paths**: Directories specified in `plugin_dirs`
4. **Environment**: Paths from `ARTE_PLUGIN_DIRS`

Example with multiple paths:

```toml
plugin_dirs = [
    "./plugins",
    "./team-plugins",
    "C:/shared/artreactor-plugins"
]
```

## Plugin-Specific Configuration

### Enabling/Disabling Plugins

```toml
[plugins.my-plugin]
enabled = false  # Disable this plugin
```

### Plugin Priority

Higher priority plugins load first:

```toml
[plugins.core-foundation]
priority = 1000  # Loads first

[plugins.optional-feature]
priority = 50    # Loads later
```

### Plugin Settings

Pass custom settings to plugins:

```toml
[plugins.blender-integration]
enabled = true

[plugins.blender-integration.settings]
blender_path = "C:/Program Files/Blender Foundation/Blender 3.6/blender.exe"
auto_launch = true
port = 9000
```

Access these in your plugin:

```python
async def initialize(self):
    config = self.context.get("config", {})
    plugin_config = config.get("plugins", {}).get("blender-integration", {})
    settings = plugin_config.get("settings", {})
    
    blender_path = settings.get("blender_path")
    auto_launch = settings.get("auto_launch", False)
```

## Logging Configuration

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical errors that may cause shutdown

### Log Providers

#### Console Logging

```toml
[logging]
providers = ["console"]
level = "INFO"
```

#### File Logging

```toml
[logging]
providers = ["console", "file"]

[logging.file]
path = "logs/artreactor.log"
max_bytes = 10485760  # 10MB
backup_count = 5
```

#### Custom Logging

```toml
[logging]
providers = ["console", "custom"]

[logging.custom]
handler = "my_plugin.logging.CustomHandler"
level = "DEBUG"
```

## Security Configuration

### API Keys

Store sensitive keys securely:

```toml
[security]
enable_auth = true
api_key = "${ARTREACTOR_API_KEY}"  # From environment variable
```

### Permissions

Configure plugin permissions:

```toml
[plugins.file-operations]
enabled = true

[plugins.file-operations.permissions]
allowed_paths = [
    "C:/Projects/Assets",
    "D:/GameData"
]
deny_patterns = ["*.exe", "*.dll"]
```

## Example Configurations

### Development Environment

```toml
debug = true
plugin_dirs = ["./plugins", "./dev-plugins"]

[logging]
level = "DEBUG"
providers = ["console"]

[server]
host = "127.0.0.1"
port = 8000
reload = true
```

### Production Environment

```toml
debug = false
plugin_dirs = ["./plugins"]

[logging]
level = "INFO"
providers = ["console", "file"]

[logging.file]
path = "/var/log/artreactor/app.log"
max_bytes = 52428800  # 50MB
backup_count = 10

[server]
host = "0.0.0.0"
port = 8000
workers = 8
reload = false

[security]
enable_auth = true
api_key = "${ARTREACTOR_API_KEY}"
```

### Studio Pipeline Configuration

```toml
plugin_dirs = [
    "./plugins",
    "//studio-server/shared/artreactor-plugins"
]

[plugins.perforce-integration]
enabled = true
[plugins.perforce-integration.settings]
p4_port = "perforce.studio.com:1666"
p4_user = "${P4USER}"
p4_client = "${P4CLIENT}"

[plugins.maya-integration]
enabled = true
[plugins.maya-integration.settings]
maya_versions = ["2023", "2024"]
auto_launch = false

[plugins.unreal-integration]
enabled = true
[plugins.unreal-integration.settings]
engine_path = "C:/Program Files/Epic Games/UE_5.3"
project_path = "//studio-server/projects/MainGame/MainGame.uproject"

[logging]
level = "INFO"
providers = ["console", "file"]

[logging.file]
path = "//studio-server/logs/artreactor/${COMPUTERNAME}.log"
```

## Validation

Validate your configuration:

```bash
arte config validate
```

View the current effective configuration:

```bash
arte config show
```

## Best Practices

1. **Use Environment Variables for Secrets**: Never commit API keys or passwords
2. **Separate Configs per Environment**: Use different config files for dev/prod
3. **Document Custom Settings**: Add comments explaining plugin-specific settings
4. **Version Control**: Commit `config.toml.example` with safe defaults
5. **Validate After Changes**: Always validate configuration before deploying
