# Development Setup

## Prerequisites

- Python 3.10+
- Git
- uv package manager

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/josephkirk/ArtReactorCore.git
   cd ArtReactorCore
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run tests:
   ```bash
   uv run pytest
   ```

## Development Workflow

1. Create a feature branch
2. Make changes
3. Run tests and linting
4. Submit pull request

See [Testing](testing.md) for test guidelines.
