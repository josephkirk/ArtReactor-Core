import typer
import uvicorn
import shutil
import os
from pathlib import Path
from typing import Optional
from enum import Enum

import toml

app = typer.Typer(name="arte", help="ArteCore CLI")
plugin_app = typer.Typer(name="plugin", help="Manage plugins")
app.add_typer(plugin_app, name="plugin")


class PluginType(str, Enum):
    CORE = "core"
    ROUTER = "router"
    APP = "app"
    MODEL = "model"
    AGENT = "agent"
    UI = "ui"


# Plugin type descriptions (shared across commands)
PLUGIN_TYPE_DESCRIPTIONS = {
    PluginType.CORE: "Core plugins extend fundamental ArtReactor functionality",
    PluginType.ROUTER: "Router plugins add new API endpoints and routes",
    PluginType.APP: "App plugins integrate external applications",
    PluginType.MODEL: "Model plugins provide AI model integrations",
    PluginType.AGENT: "Agent plugins add new agent capabilities",
    PluginType.UI: "UI plugins provide web-based user interfaces",
}


def _render_template(template_path: Path, dest_path: Path, template_vars: dict) -> bool:
    """Render a template file with variable substitution.

    Args:
        template_path: Path to the template file
        dest_path: Path where the rendered file should be written
        template_vars: Dictionary of template variables to substitute

    Returns:
        True if successful, False otherwise
    """
    try:
        if not template_path.exists():
            return False

        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
            for k, v in template_vars.items():
                content = content.replace(k, v)

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except (IOError, OSError) as e:
        typer.echo(f"Error rendering template {template_path.name}: {e}", err=True)
        return False


@app.command()
def start(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable hot reload"),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to config file"
    ),
):
    """Start the ArteCore service."""
    if config:
        os.environ["ARTE_CONFIG_PATH"] = str(config.resolve())
        typer.echo(f"Using config file: {config}")

    typer.echo(f"Starting ArteCore on {host}:{port}...")

    # Patch stdout/stderr for --noconsole mode
    import sys

    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    uvicorn.run(
        "artreactor.app:app", host=host, port=port, reload=reload, use_colors=False
    )


@plugin_app.command("install")
def install_plugin(
    path: str = typer.Argument(
        ..., help="Path to local directory or Git URL of the plugin to install"
    ),
    link: bool = typer.Option(
        False, "--link", "-l", help="Create a symlink instead of copying (dev mode)"
    ),
):
    """Install a plugin from a local directory or Git URL."""
    try:
        # Validate --link is only used with local paths
        if link and (path.startswith("http") or path.startswith("git@")):
            typer.echo(
                "Error: The --link flag is only supported for local paths, not for Git URLs.",
                err=True,
            )
            raise typer.Exit(code=1)

        # Check if it's a URL
        if path.startswith("http") or path.startswith("git@"):
            # It's a git repo
            repo_name = path.split("/")[-1].replace(".git", "")
            # It's a git repo
            repo_name = path.split("/")[-1].replace(".git", "")
            dest_dir = Path("plugins") / repo_name

            if dest_dir.exists():
                typer.echo(
                    f"Error: Plugin {repo_name} already exists at {dest_dir}", err=True
                )
                raise typer.Exit(code=1)

            typer.echo(f"Cloning plugin from {path} to {dest_dir}...")
            # Use subprocess to run git clone
            import subprocess

            subprocess.run(["git", "clone", path, str(dest_dir)], check=True)
            typer.echo(f"Plugin cloned to {dest_dir}")

        else:
            # Local path
            local_path = Path(path).resolve()
            if not local_path.exists():
                typer.echo(f"Error: Path {local_path} does not exist.", err=True)
                raise typer.Exit(code=1)

            # Auto-detect plugin structure
            # Check if root has plugin.toml
            if (local_path / "plugin.toml").exists():
                # Root is the plugin itself
                plugin_name = local_path.name
                source_path = local_path
            # Check if plugins/<name>/plugin.toml exists
            elif (local_path / "plugins").exists():
                # Find plugins in plugins directory
                plugins_path = local_path / "plugins"
                plugin_dirs = [
                    d
                    for d in plugins_path.iterdir()
                    if d.is_dir() and (d / "plugin.toml").exists()
                ]
                if not plugin_dirs:
                    typer.echo(
                        f"Error: No plugin.toml found in {local_path} or {local_path / 'plugins'}/*",
                        err=True,
                    )
                    raise typer.Exit(code=1)
                if len(plugin_dirs) > 1:
                    typer.echo(
                        "Error: Multiple plugins found. Please install plugins individually.",
                        err=True,
                    )
                    typer.echo(
                        f"Found: {', '.join(d.name for d in plugin_dirs)}", err=True
                    )
                    typer.echo(
                        f"Example: arte plugin install {local_path / 'plugins' / plugin_dirs[0].name}",
                        err=True,
                    )
                    raise typer.Exit(code=1)
                source_path = plugin_dirs[0]
                plugin_name = source_path.name
            else:
                typer.echo(
                    f"Error: No plugin.toml found at {local_path} or {local_path / 'plugins'}/*",
                    err=True,
                )
                typer.echo(
                    "Did you run 'arte plugin create' or 'arte plugin init-project'?",
                    err=True,
                )
                raise typer.Exit(code=1)

            dest_dir = Path("plugins") / plugin_name

            if dest_dir.exists():
                typer.echo(
                    f"Error: Plugin {plugin_name} already exists at {dest_dir}",
                    err=True,
                )
                raise typer.Exit(code=1)

            # Ensure plugins directory exists
            Path("plugins").mkdir(exist_ok=True)

            if link:
                # Create link for dev mode
                # On Windows, use junctions (do not require admin) instead of symlinks
                typer.echo(f"Linking plugin {plugin_name} from {source_path}...")
                if not source_path.is_dir():
                    typer.echo(
                        f"Error: Source path {source_path} is not a directory.",
                        err=True,
                    )
                    raise typer.Exit(code=1)

                import sys
                import subprocess

                try:
                    if sys.platform == "win32":
                        # Use junction on Windows (no admin required)
                        result = subprocess.run(
                            [
                                "cmd",
                                "/c",
                                "mklink",
                                "/J",
                                str(dest_dir),
                                str(source_path),
                            ],
                            capture_output=True,
                            text=True,
                        )
                        if result.returncode != 0:
                            raise OSError(result.stderr or "Failed to create junction")
                        typer.echo(f"Plugin linked (junction) to {dest_dir}")
                    else:
                        # Use symlink on Unix
                        dest_dir.symlink_to(source_path, target_is_directory=True)
                        typer.echo(f"Plugin linked to {dest_dir}")
                except OSError as e:
                    typer.echo(f"Error creating link: {e}", err=True)
                    raise typer.Exit(code=1)
            else:
                # Copy the plugin
                typer.echo(f"Installing plugin {plugin_name} from {source_path}...")
                shutil.copytree(source_path, dest_dir)
                typer.echo(f"Plugin installed to {dest_dir}")

        # Check for dependencies
        manifest_path = dest_dir / "plugin.toml"
        if manifest_path.exists():
            data = toml.load(manifest_path)
            deps = data.get("dependencies", [])
            if deps:
                typer.echo("Plugin has dependencies:")
                for d in deps:
                    typer.echo(f"  - {d}")
                typer.echo("Run the build script to resolve dependencies.")
    except Exception as e:
        typer.echo(f"Installation failed: {e}", err=True)
        raise typer.Exit(code=1)


@plugin_app.command("create")
def create_plugin(
    name: str = typer.Argument(..., help="Name of the plugin"),
    type: PluginType = typer.Option(PluginType.UI, help="Type of plugin"),
    destination: Optional[Path] = typer.Option(
        None, help="Directory to create the plugin in. Defaults to current directory."
    ),
):
    """Create a new plugin from a template."""

    # Determine destination directory
    # Default to "plugins/name" if destination not provided?
    # Or strict adherence to CWD?
    # User said "src/artreactor/plugins is assume ... it should be root folder instead"
    # Usually "root folder" implies relative to project root.
    # If I default to plugins/name, that's cleaner.

    if destination:
        dest_dir = destination / name
    else:
        dest_dir = Path("plugins") / name

    if dest_dir.exists():
        typer.echo(f"Error: Plugin directory {dest_dir} already exists.", err=True)
        raise typer.Exit(code=1)

    dest_dir.mkdir(parents=True)

    # Locate templates
    # This assumes the cli module is at src/artreactor/cli
    template_root = Path(__file__).parent.parent / "plugins" / "templates"

    if not template_root.exists():
        # Fallback for dev environment or if templates not packaged yet?
        # For now, assume they exist.
        typer.echo(f"Error: Templates directory not found at {template_root}", err=True)
        raise typer.Exit(code=1)

    template_vars = {
        "{{name}}": name,
        "{{description}}": f"A {type.value} plugin named {name}",
        "{{type}}": type.value,
    }

    if type == PluginType.UI:
        # Copy UI template
        tmpl_dir = template_root / "ui"

        # Manifest
        with open(tmpl_dir / "plugin.toml", "r") as f:
            content = f.read()
            for k, v in template_vars.items():
                content = content.replace(k, v)
        with open(dest_dir / "plugin.toml", "w") as f:
            f.write(content)

        # Dist/Index.html
        (dest_dir / "dist").mkdir()
        with open(tmpl_dir / "dist" / "index.html", "r") as f:
            content = f.read()
            for k, v in template_vars.items():
                content = content.replace(k, v)
        with open(dest_dir / "dist" / "index.html", "w") as f:
            f.write(content)

    elif type == PluginType.ROUTER:
        # Copy Router template
        tmpl_dir = template_root / "router"
        class_name = "".join(x.title() for x in name.replace("-", "_").split("_"))
        template_vars["{{class_name}}"] = class_name

        # Manifest
        with open(tmpl_dir / "plugin.toml", "r") as f:
            content = f.read()
            for k, v in template_vars.items():
                content = content.replace(k, v)
        with open(dest_dir / "plugin.toml", "w") as f:
            f.write(content)

        # __init__.py
        with open(tmpl_dir / "__init__.py", "r") as f:
            content = f.read()
            for k, v in template_vars.items():
                content = content.replace(k, v)
        with open(dest_dir / "__init__.py", "w") as f:
            f.write(content)

        # SKILL.md
        skill_tmpl = tmpl_dir / "SKILL.md"
        if skill_tmpl.exists():
            with open(skill_tmpl, "r") as f:
                content = f.read()
                for k, v in template_vars.items():
                    content = content.replace(k, v)
            with open(dest_dir / "SKILL.md", "w") as f:
                f.write(content)

    else:
        # Default Python Plugin Template
        def_tmpl_dir = template_root / "default"

        # Variables for __init__.py
        class_name = "".join(x.title() for x in name.replace("-", "_").split("_"))

        base_class = "Plugin"
        import_str = (
            "from artreactor.core.interfaces.plugin import Plugin, PluginManifest"
        )
        extra_methods = ""

        if type == PluginType.APP:
            base_class = "AppPlugin"
            import_str = "from artreactor.core.interfaces.plugin import AppPlugin, PluginManifest"
            extra_methods = """
    async def launch(self) -> bool:
        return True

    async def execute_code(self, code: str) -> Any:
        return None
"""

        template_vars.update(
            {
                "{{class_name}}": class_name,
                "{{base_class}}": base_class,
                "{{imports}}": import_str,
                "{{extra_methods}}": extra_methods,
            }
        )

        # Manifest
        with open(def_tmpl_dir / "plugin.toml", "r") as f:
            content = f.read()
            for k, v in template_vars.items():
                content = content.replace(k, v)
        with open(dest_dir / "plugin.toml", "w") as f:
            f.write(content)

        # __init__.py
        with open(def_tmpl_dir / "__init__.py", "r") as f:
            content = f.read()
            for k, v in template_vars.items():
                content = content.replace(k, v)
        with open(dest_dir / "__init__.py", "w") as f:
            f.write(content)

        # SKILL.md
        skill_tmpl = def_tmpl_dir / "SKILL.md"
        if skill_tmpl.exists():
            with open(skill_tmpl, "r") as f:
                content = f.read()
                for k, v in template_vars.items():
                    content = content.replace(k, v)
            with open(dest_dir / "SKILL.md", "w") as f:
                f.write(content)

    typer.echo(f"Created plugin {name} of type {type.value} at {dest_dir}")


@plugin_app.command("init-project")
def init_project(
    name: str = typer.Argument(..., help="Name of the plugin project"),
    type: PluginType = typer.Option(PluginType.CORE, help="Type of plugin"),
):
    """Initialize a new standalone plugin repository with project scaffolding."""

    # Check if current directory is empty or looks like a fresh repo
    current_dir = Path.cwd()
    existing_files = list(current_dir.iterdir())

    # Filter out common VCS files (but not README.md - we want to warn about that)
    vcs_files = {".git", ".gitignore", "LICENSE"}
    non_vcs_files = [f for f in existing_files if f.name not in vcs_files]

    if non_vcs_files:
        typer.echo(
            "Warning: Current directory is not empty. This command will create new files.",
            err=True,
        )
        if not typer.confirm("Do you want to continue?"):
            raise typer.Exit(code=0)

    typer.echo(f"Initializing plugin project '{name}' with type '{type.value}'...")

    # 1. Ensure plugins/ directory exists
    plugins_dir = current_dir / "plugins"
    plugins_dir.mkdir(exist_ok=True)

    # 2. Create the plugin itself using existing create_plugin logic
    try:
        # Create plugin (defaults to plugins/ directory)
        create_plugin(name=name, type=type, destination=None)
    except Exception as e:
        typer.echo(f"Error creating plugin: {e}", err=True)
        raise typer.Exit(code=1)

    # 3. Generate project files
    template_root = Path(__file__).parent.parent / "plugins" / "templates" / "project"

    if not template_root.exists():
        typer.echo(f"Error: Project templates not found at {template_root}", err=True)
        raise typer.Exit(code=1)

    # Template variables for project scaffolding
    # Note: Both {{name}} and {{plugin_name}} are used for clarity in different contexts
    # {{name}} = project/package name, {{plugin_name}} = the plugin directory name
    template_vars = {
        "{{name}}": name,
        "{{description}}": f"ArtReactor {type.value} plugin",
        "{{plugin_name}}": name,
        "{{type}}": type.value,
        "{{type_description}}": PLUGIN_TYPE_DESCRIPTIONS.get(type, ""),
    }

    # Generate pyproject.toml
    if _render_template(
        template_root / "pyproject.toml.template",
        current_dir / "pyproject.toml",
        template_vars,
    ):
        typer.echo("  ✓ Created pyproject.toml")
    else:
        typer.echo("  ✗ Failed to create pyproject.toml", err=True)

    # Generate README.md
    if _render_template(
        template_root / "README.md.template", current_dir / "README.md", template_vars
    ):
        typer.echo("  ✓ Created README.md")
    else:
        typer.echo("  ✗ Failed to create README.md", err=True)

    # Generate .gitignore
    if _render_template(
        template_root / "gitignore.template", current_dir / ".gitignore", template_vars
    ):
        typer.echo("  ✓ Created .gitignore")
    else:
        typer.echo("  ✗ Failed to create .gitignore", err=True)

    # Generate tests/
    tests_dir = current_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    if _render_template(
        template_root / "test_plugin_load.py.template",
        tests_dir / "test_plugin_load.py",
        template_vars,
    ):
        typer.echo("  ✓ Created tests/test_plugin_load.py")
    else:
        typer.echo("  ✗ Failed to create tests/test_plugin_load.py", err=True)

    # Create __init__.py for tests
    (tests_dir / "__init__.py").touch()

    typer.echo(f"\n✓ Successfully initialized plugin project '{name}'!")
    typer.echo("\nNext steps:")
    typer.echo("  1. Install dependencies: pip install -e .")
    typer.echo(f"  2. Edit your plugin: plugins/{name}/__init__.py")
    typer.echo("  3. Run tests: pytest")
    typer.echo(
        f"  4. Install into a host project: arte plugin install /path/to/{name} --link"
    )


@plugin_app.command("templates")
def list_templates():
    """List available plugin templates."""
    typer.echo("Available plugin templates:\n")

    for plugin_type, description in PLUGIN_TYPE_DESCRIPTIONS.items():
        typer.echo(f"  {plugin_type.value:12} - {description}")

    typer.echo("\nUsage:")
    typer.echo("  arte plugin create <name> --type <template>")
    typer.echo("  arte plugin init-project <name> --type <template>")


if __name__ == "__main__":
    app()
