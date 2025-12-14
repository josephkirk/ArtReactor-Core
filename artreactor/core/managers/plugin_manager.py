import toml
import importlib
import importlib.util
import logging
import inspect
import sys
from typing import Dict, List, Optional, Type, Any, Union, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from artreactor.core.interfaces.logging_plugin import LoggingPlugin
    from artreactor.core.interfaces.telemetry_plugin import TelemetryPlugin

from artreactor.core.interfaces.plugin import (
    Plugin,
    PluginManifest,
    PluginTiming,
    PluginType,
    CorePlugin,
    RouterPlugin,
    AppPlugin,
    UiPlugin,
)

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(
        self,
        plugin_dirs: List[str] = None,
        plugin_dir: Union[str, Path] = None,
        config_path: Optional[str] = None,
        context: Any = None,
        skill_manager: Any = None,
    ):
        self.plugin_dirs = []

        if plugin_dirs:
            self.plugin_dirs.extend([Path(d) for d in plugin_dirs])

        if plugin_dir:
            self.plugin_dirs.append(Path(plugin_dir))

        if not self.plugin_dirs:
            # Default to including both potential local plugins and src/artreactor/plugins
            self.plugin_dirs = [Path("plugins"), Path("src/artreactor/plugins")]

        self.config_path = Path(config_path) if config_path else None
        self.context = context
        self.skill_manager = skill_manager
        self.plugins: Dict[str, Plugin] = {}
        self.manifests: Dict[str, PluginManifest] = {}
        self._load_order: List[str] = []

        # Load extra plugin dirs from config
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = toml.load(f)

                extra_dirs = config.get("plugin_dirs", [])
                for d in extra_dirs:
                    path = Path(d)
                    if path not in self.plugin_dirs:
                        self.plugin_dirs.append(path)

                # Auto-install plugins with sources
                self._install_missing_plugins(config.get("plugins", {}))

            except Exception as e:
                logger.error(
                    f"Failed to load plugin config from {self.config_path}: {e}"
                )

    def _install_missing_plugins(self, plugins_config: Dict[str, Any]):
        import subprocess

        # Determine install directory (prefer "plugins", else first dir)
        install_dir = next(
            (d for d in self.plugin_dirs if d.name == "plugins"), self.plugin_dirs[0]
        )
        if not install_dir.exists():
            try:
                install_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create install dir {install_dir}: {e}")
                return

        for name, conf in plugins_config.items():
            source = conf.get("source")
            if not source:
                continue

            # Check if plugin exists in any plugin dir
            exists = False
            for p_dir in self.plugin_dirs:
                if (p_dir / name).exists():
                    exists = True
                    break

            if exists:
                continue

            logger.info(f"Auto-installing missing plugin {name} from {source}...")
            target_path = install_dir / name
            try:
                # Assume git source for now
                if source.startswith("http") or source.startswith("git@"):
                    subprocess.run(
                        ["git", "clone", source, str(target_path)],
                        check=True,
                        capture_output=True,
                    )
                    logger.info(f"Successfully installed {name} to {target_path}")
                else:
                    logger.warning(f"Unknown source format for {name}: {source}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {name}: {e.stderr.decode()}")
            except Exception as e:
                logger.error(f"Failed to install {name}: {e}")

    def discover_plugins(self) -> List[PluginManifest]:
        """Scans the plugin directory for valid plugins."""
        manifests = []
        for p_dir in self.plugin_dirs:
            if not p_dir.exists():
                logger.debug(f"Plugin directory {p_dir} does not exist, skipping.")
                continue

            # Look for plugins recursively
            # We search for all plugin.toml files
            for manifest_path in p_dir.rglob("plugin.toml"):
                # Skip templates directory
                if "templates" in manifest_path.parts:
                    continue

                try:
                    manifest = self._load_manifest(manifest_path)
                    # Set the plugin path to the directory containing plugin.toml
                    manifest.path = str(manifest_path.parent.resolve())
                    manifests.append(manifest)
                except Exception as e:
                    # Use relative path for better logging if possible
                    try:
                        rel_path = manifest_path.relative_to(p_dir)
                    except ValueError:
                        rel_path = manifest_path.name
                    logger.error(f"Failed to load manifest for {rel_path}: {e}")

        # Filter/Override based on config
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = toml.load(f)

                plugins_config = config.get("plugins", {})
                final_manifests = []

                for manifest in manifests:
                    p_config = plugins_config.get(manifest.name, {})

                    # Check if enabled (default to True if not specified in config,
                    # unless strict mode is implemented, but spec says "respect central config")
                    # Let's assume enabled by default unless explicitly disabled in config
                    if p_config.get("enabled", True) is False:
                        logger.info(f"Plugin {manifest.name} disabled by config.")
                        continue

                    # Apply overrides
                    if "priority" in p_config:
                        manifest.priority = p_config["priority"]
                    if "timing" in p_config:
                        manifest.timing = PluginTiming(p_config["timing"])

                    final_manifests.append(manifest)
                return final_manifests
            except Exception as e:
                logger.error(
                    f"Failed to load plugin config from {self.config_path}: {e}"
                )
                return manifests

        return manifests

        return manifests

    def _load_manifest(self, path: Path) -> PluginManifest:
        with open(path, "r") as f:
            data = toml.load(f)

        # Convert string enums
        data["type"] = PluginType(data["type"])
        if "timing" in data:
            data["timing"] = PluginTiming(data["timing"])

        manifest = PluginManifest(**data)

        # Load SKILL.md if it exists
        skill_path = path.parent / "SKILL.md"
        if skill_path.exists():
            from artreactor.core.utils.skill_parser import parse_skill_md

            manifest.skill = parse_skill_md(skill_path, manifest.name)
            if manifest.skill:
                logger.info(f"Loaded skill definition for plugin {manifest.name}")

        return manifest

    async def load_plugins(self, timing: PluginTiming = PluginTiming.DEFAULT):
        """Loads plugins for the specified timing phase."""
        discovered = self.discover_plugins()

        # Filter by timing
        to_load = [m for m in discovered if m.timing == timing]

        # Sort by priority (Higher first)
        to_load.sort(key=lambda m: m.priority, reverse=True)

        for manifest in to_load:
            if manifest.name in self.plugins:
                continue  # Already loaded

            try:
                await self._load_plugin(manifest)
            except Exception as e:
                logger.error(f"Failed to load plugin {manifest.name}: {e}")

    async def _load_plugin(self, manifest: PluginManifest):
        # Use plugin name as module name, or construct a consistent one
        module_name = f"artreactor.plugins.{manifest.name.replace('-', '_')}"
        plugin_dir = Path(manifest.path)

        # Determine valid entry file
        init_file = plugin_dir / "__init__.py"
        entry_file = plugin_dir / manifest.entry_point if manifest.entry_point else None

        target_file = None
        if entry_file and entry_file.exists():
            target_file = entry_file
        elif init_file.exists():
            target_file = init_file

        # If no python file, check if it is a UI plugin (declarative)
        if not target_file:
            if manifest.type == PluginType.UI:
                # Declarative UI plugin, no code to load
                module = None
            else:
                raise FileNotFoundError(
                    f"No entry point found for plugin {manifest.name} at {plugin_dir}"
                )
        else:
            try:
                spec = importlib.util.spec_from_file_location(module_name, target_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                else:
                    raise ImportError(f"Could not load spec for {target_file}")
            except Exception as e:
                logger.error(f"Failed to load module from {target_file}: {e}")
                raise

        plugin_class = None
        if module:
            # Find Plugin class
            plugin_class = self._find_plugin_class(module)

        if plugin_class is None:
            if manifest.type == PluginType.UI:
                logger.info(
                    f"No Plugin class found for UI plugin {manifest.name}, treating as declarative."
                )
                plugin_class = UiPlugin
            else:
                raise ValueError(f"No Plugin class found in {module_name}")

        try:
            # Instantiate
            plugin = plugin_class(manifest, self.context)

            # Initialize
            await plugin.initialize()

            # Scan for tools
            self._scan_for_tools(plugin)

            # Register skill if available
            if manifest.skill and self.skill_manager:
                self.skill_manager.register_skill(manifest.skill)

            self.plugins[manifest.name] = plugin
            self.manifests[manifest.name] = manifest
            self._load_order.append(manifest.name)
            logger.info(f"Successfully loaded plugin: {manifest.name}")

        except Exception as e:
            logger.error(f"Failed to initialize plugin {manifest.name}: {e}")
            raise

    def _scan_for_tools(self, plugin: Plugin):
        """Scans the plugin instance for methods decorated with @tool."""
        from artreactor.core.decorators import ToolDefinition

        for name, method in inspect.getmembers(plugin):
            if getattr(method, "_is_tool", False):
                tool_name = getattr(method, "_tool_name", None) or name
                tool_desc = getattr(
                    method, "_tool_description", None
                ) or inspect.getdoc(method)

                # Check for duplicates
                if any(t.name == tool_name for t in plugin.tools):
                    logger.error(
                        f"Duplicate tool name '{tool_name}' in plugin {plugin.manifest.name}"
                    )
                    raise ValueError(
                        f"Duplicate tool name '{tool_name}' in plugin {plugin.manifest.name}"
                    )

                tool_def = ToolDefinition(
                    func=method, name=tool_name, description=tool_desc
                )
                plugin.tools.append(tool_def)
                logger.debug(
                    f"Discovered tool '{tool_name}' in plugin {plugin.manifest.name}"
                )

    def _find_plugin_class(self, module) -> Optional[Type[Plugin]]:
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Plugin)
                and obj is not Plugin
                and obj is not CorePlugin
                and obj is not RouterPlugin
                and obj is not AppPlugin
                and obj is not UiPlugin
            ):
                return obj
        return None

    def get_plugin(self, name: str) -> Optional[Plugin]:
        return self.plugins.get(name)

    def get_plugins_by_type(self, type: PluginType) -> List[Plugin]:
        return [p for p in self.plugins.values() if p.manifest.type == type]

    def get_all_plugins(self) -> List[PluginManifest]:
        return list(self.manifests.values())

    async def shutdown_all(self):
        # Shutdown in reverse load order
        for name in reversed(self._load_order):
            plugin = self.plugins.get(name)
            if plugin:
                try:
                    await plugin.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down plugin {name}: {e}")

    def get_logging_plugins(self) -> List["LoggingPlugin"]:
        from artreactor.core.interfaces.logging_plugin import LoggingPlugin

        return [p for p in self.plugins.values() if isinstance(p, LoggingPlugin)]

    def get_telemetry_plugins(self) -> List["TelemetryPlugin"]:
        from artreactor.core.interfaces.telemetry_plugin import TelemetryPlugin

        return [p for p in self.plugins.values() if isinstance(p, TelemetryPlugin)]

    def get_all_dependencies_from_manifests(self) -> List[str]:
        """Scans and returns all dependencies from all valid plugin manifests."""
        manifests = self.discover_plugins()
        deps = set()
        for manifest in manifests:
            deps.update(manifest.dependencies)
        return list(deps)
