"""Integration tests for skill loading from plugins."""

import pytest
from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.core.managers.skill_manager import SkillManager
from artreactor.models.plugin import PluginTiming


@pytest.mark.asyncio
async def test_plugin_with_skill_loads(tmp_path):
    """Test that a plugin with SKILL.md file loads correctly."""
    # Create a test plugin directory
    plugin_dir = tmp_path / "test-plugin"
    plugin_dir.mkdir()

    # Create plugin.toml
    (plugin_dir / "plugin.toml").write_text("""
name = "test-plugin"
version = "1.0.0"
type = "router"
description = "Test plugin"
""")

    # Create __init__.py
    (plugin_dir / "__init__.py").write_text("""
from typing import Any
from fastapi import APIRouter
from artreactor.core.interfaces.plugin import RouterPlugin, PluginManifest

class TestPlugin(RouterPlugin):
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)
        self.router = APIRouter()
        
        @self.router.get("/")
        async def root():
            return {"message": "Hello from test-plugin!"}

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    def get_router(self) -> APIRouter:
        return self.router
""")

    # Create SKILL.md with YAML frontmatter (Anthropic format)
    (plugin_dir / "SKILL.md").write_text("""---
name: Test Plugin Skill
description: This is a test skill for the test plugin
---

## Context Keywords

- testing
- example

## Tools

- `test_plugin_root`

## Instructions

Use this plugin for testing purposes.

## Examples

```python
result = await test_plugin_root()
```
""")

    # Create managers
    skill_manager = SkillManager()
    plugin_manager = PluginManager(plugin_dir=tmp_path, skill_manager=skill_manager)

    # Load plugins
    await plugin_manager.load_plugins(PluginTiming.DEFAULT)

    # Verify plugin loaded
    assert "test-plugin" in plugin_manager.plugins

    # Verify skill was registered
    skill = skill_manager.get_skill("Test Plugin Skill")
    assert skill is not None
    assert skill.plugin_name == "test-plugin"
    assert "testing" in skill.context_keywords
    assert "test_plugin_root" in skill.tools

    # Cleanup
    await plugin_manager.shutdown_all()


@pytest.mark.asyncio
async def test_plugin_without_skill_loads(tmp_path):
    """Test that a plugin without SKILL.md still loads correctly."""
    # Create a test plugin directory
    plugin_dir = tmp_path / "no-skill-plugin"
    plugin_dir.mkdir()

    # Create plugin.toml
    (plugin_dir / "plugin.toml").write_text("""
name = "no-skill-plugin"
version = "1.0.0"
type = "router"
description = "Plugin without skill"
""")

    # Create __init__.py
    (plugin_dir / "__init__.py").write_text("""
from typing import Any
from fastapi import APIRouter
from artreactor.core.interfaces.plugin import RouterPlugin, PluginManifest

class NoSkillPlugin(RouterPlugin):
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)
        self.router = APIRouter()

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    def get_router(self) -> APIRouter:
        return self.router
""")

    # Create managers
    skill_manager = SkillManager()
    plugin_manager = PluginManager(plugin_dir=tmp_path, skill_manager=skill_manager)

    # Load plugins
    await plugin_manager.load_plugins(PluginTiming.DEFAULT)

    # Verify plugin loaded
    assert "no-skill-plugin" in plugin_manager.plugins

    # Verify no skill was registered for this plugin
    assert len(skill_manager.skills) == 0

    # Cleanup
    await plugin_manager.shutdown_all()


@pytest.mark.asyncio
async def test_skill_context_matching(tmp_path):
    """Test that skills can be matched by context."""
    # Create a test plugin
    plugin_dir = tmp_path / "git-plugin"
    plugin_dir.mkdir()

    (plugin_dir / "plugin.toml").write_text("""
name = "git-plugin"
version = "1.0.0"
type = "router"
description = "Git control plugin"
""")

    (plugin_dir / "__init__.py").write_text("""
from typing import Any
from fastapi import APIRouter
from artreactor.core.interfaces.plugin import RouterPlugin, PluginManifest

class GitPlugin(RouterPlugin):
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)
        self.router = APIRouter()

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    def get_router(self) -> APIRouter:
        return self.router
""")

    (plugin_dir / "SKILL.md").write_text("""---
name: Git Control
description: Provides version control operations
---

## Context Keywords

- git
- version control
- repository

## Tools

- `git_status`
- `git_commit`

## Instructions

Use this skill for Git operations.
""")

    # Create managers
    skill_manager = SkillManager()
    plugin_manager = PluginManager(plugin_dir=tmp_path, skill_manager=skill_manager)

    # Load plugins
    await plugin_manager.load_plugins(PluginTiming.DEFAULT)

    # Test context matching
    matches = skill_manager.get_skills_by_context("I need to check git status")
    assert len(matches) == 1
    assert matches[0].name == "Git Control"

    matches = skill_manager.get_skills_by_context("version control operations")
    assert len(matches) == 1

    matches = skill_manager.get_skills_by_context("unrelated task")
    assert len(matches) == 0

    # Cleanup
    await plugin_manager.shutdown_all()
