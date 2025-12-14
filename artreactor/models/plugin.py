"""Plugin models for ArtReactor Core.

This module contains models related to the plugin system,
including plugin types, timing, and manifest structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PluginType(str, Enum):
    """Type of plugin."""

    CORE = "core"
    ROUTER = "router"
    APP = "app"
    MODEL = "model"
    AGENT = "agent"
    UI = "ui"


class PluginTiming(str, Enum):
    """When the plugin should be loaded."""

    PRE_INIT = "pre-init"
    DEFAULT = "default"
    AFTER_INIT = "after-init"


@dataclass
class AgentSkill:
    """Agent skill definition from SKILL.md file."""

    name: str
    description: str
    context_keywords: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    instructions: str = ""
    examples: List[str] = field(default_factory=list)
    plugin_name: Optional[str] = None


@dataclass
class PluginManifest:
    """Plugin manifest containing metadata and configuration."""

    name: str
    version: str
    type: PluginType
    timing: PluginTiming = PluginTiming.DEFAULT
    priority: int = 0
    description: Optional[str] = None
    entry_point: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    dependencies: List[str] = field(default_factory=list)

    # Source Control fields
    provider: Optional[str] = None
    path: Optional[str] = None

    # Agent Skills field
    skill: Optional[AgentSkill] = None

    @property
    def module_name(self) -> str:
        """Get the Python module name from the plugin name."""
        return self.name.replace("-", "_")
