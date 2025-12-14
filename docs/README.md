# ArtReactor Core Documentation

This directory contains the source files for the ArtReactor Core documentation site.

## Documentation Structure

```
docs/
├── index.md                      # Home page
├── getting-started/              # Installation and setup guides
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── architecture/                 # Architecture documentation
│   ├── overview.md
│   ├── core-components.md
│   ├── plugin-system.md
│   ├── event-system.md
│   └── data-flow.md
├── use-cases/                    # Real-world examples
│   ├── overview.md
│   ├── game-asset-pipeline.md
│   ├── dcc-integration.md
│   └── agentic-workflows.md
├── plugin-development/           # Plugin development guides
│   ├── getting-started.md
│   ├── plugin-types.md
│   ├── creating-plugins.md
│   ├── tools-and-decorators.md
│   ├── agent-skills.md
│   └── best-practices.md
├── api/                          # API reference
│   ├── cli.md
│   └── interfaces.md
├── advanced/                     # Advanced topics
│   ├── logging-telemetry.md
│   └── database-manager.md
└── contributing/                 # Contributing guidelines
    ├── development.md
    └── testing.md
```

## Building Documentation Locally

### Prerequisites

Install documentation dependencies:

```bash
pip install -e ".[docs]"
```

Or install directly:

```bash
pip install mkdocs mkdocs-material pymdown-extensions
```

### Build and Serve

Serve documentation locally with live reload:

```bash
mkdocs serve
```

Then open http://127.0.0.1:8000/ in your browser.

Build static site:

```bash
mkdocs build
```

Output will be in the `site/` directory.

### Strict Mode

Build with warnings as errors (used in CI):

```bash
mkdocs build --strict
```

## Writing Documentation

### Markdown

Documentation uses standard Markdown with extensions:

- **Code blocks** with syntax highlighting
- **Admonitions** for notes, warnings, etc.
- **Mermaid diagrams** for architecture diagrams
- **Tabs** for multi-platform instructions

### Examples

#### Code Blocks

\`\`\`python
from artreactor.core.interfaces.plugin import CorePlugin

class MyPlugin(CorePlugin):
    async def initialize(self):
        pass
\`\`\`

#### Admonitions

```markdown
!!! note "Important"
    This is an important note.

!!! warning
    This is a warning.
```

#### Mermaid Diagrams

\`\`\`mermaid
graph LR
    A[Start] --> B[Process]
    B --> C[End]
\`\`\`

#### Tabs

```markdown
=== "Windows"
    Instructions for Windows

=== "macOS/Linux"
    Instructions for macOS/Linux
```

## Navigation

Navigation is defined in `mkdocs.yml` at the project root. To add a new page:

1. Create the Markdown file in the appropriate directory
2. Add it to the `nav` section in `mkdocs.yml`

Example:

```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Your New Page: getting-started/your-page.md
```

## Style Guide

### Headings

Use ATX-style headers:

```markdown
# H1 - Page Title
## H2 - Major Section
### H3 - Subsection
```

### Code

- Use `` `code` `` for inline code
- Use code blocks with language for longer examples
- Always specify the language for syntax highlighting

### Links

- Use relative links between documentation pages
- Use absolute URLs for external links

```markdown
[Internal Link](../architecture/overview.md)
[External Link](https://github.com/josephkirk/ArtReactorCore)
```

## Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to the `main` branch.

### GitHub Actions Workflow

The workflow is defined in `.github/workflows/docs.yml` and:

1. Installs MkDocs and dependencies
2. Builds the documentation
3. Deploys to GitHub Pages

### Manual Deployment

To manually deploy (requires write access):

```bash
mkdocs gh-deploy
```

## Tips

- **Preview changes**: Always preview locally before committing
- **Check links**: Ensure all internal links work
- **Test code examples**: Verify code examples are correct
- **Update navigation**: Add new pages to `mkdocs.yml`
- **Use diagrams**: Mermaid diagrams help explain architecture

## Need Help?

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material Theme Docs](https://squidfunk.github.io/mkdocs-material/)
- [Mermaid Diagram Syntax](https://mermaid.js.org/)
- [Contributing Guide](../CONTRIBUTING.md)
