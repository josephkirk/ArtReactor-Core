# Installation

This guide will help you install and set up ArtReactor Core on your system.

## Prerequisites

Before installing ArtReactor, ensure you have:

- **Python 3.10 or higher**
- **Git** (for cloning the repository)
- **uv** package manager (recommended)

### Installing uv

uv is a fast Python package manager. Install it using:

=== "Windows"
    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "macOS/Linux"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Installation Methods

### From Source (Development)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/josephkirk/ArtReactorCore.git
   cd ArtReactorCore
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Verify installation:**
   ```bash
   uv run arte --help
   ```

### From Package (Production)

!!! note "Coming Soon"
    Package distribution via PyPI is planned for future releases.

## Verifying Your Installation

Run the following command to ensure ArtReactor is correctly installed:

```bash
uv run arte --version
```

You should see output similar to:
```
ArtReactor Core v0.1.0
```

## Configuration

### Basic Configuration

Create a `config.toml` file in your project root:

```toml
# Additional plugin search paths
plugin_dirs = ["./plugins"]

# Logging Configuration
[logging]
level = "INFO"
enabled = true
providers = ["console"]
```

### Environment Variables

ArtReactor supports the following environment variables:

- `ARTE_CONFIG_PATH`: Path to custom config file
- `ARTE_PLUGIN_DIRS`: Additional plugin directories (colon-separated)

Example:
```bash
export ARTE_CONFIG_PATH=/path/to/config.toml
```

## Starting the Service

Start the ArtReactor service with:

```bash
arte start
```

By default, the service runs on `http://127.0.0.1:8000`. You can customize the host and port:

```bash
arte start --host 0.0.0.0 --port 8080
```

For development with hot-reload:

```bash
arte start --reload
```

## Next Steps

Now that ArtReactor is installed:

1. Follow the [Quick Start](quickstart.md) guide to create your first plugin
2. Explore the [Architecture](../architecture/overview.md) to understand how it works
3. Check out [Use Cases](../use-cases/overview.md) for real-world examples

## Troubleshooting

### Common Issues

#### Import Errors

If you encounter import errors, ensure you're running commands with `uv run`:

```bash
uv run arte start
```

#### Port Already in Use

If port 8000 is occupied, specify a different port:

```bash
arte start --port 8001
```

#### Permission Denied

On Windows, ensure you're running with appropriate permissions. Some operations may require administrator privileges.

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/josephkirk/ArtReactorCore/issues)
2. Search [Discussions](https://github.com/josephkirk/ArtReactorCore/discussions)
3. Open a new issue with detailed information about your problem
