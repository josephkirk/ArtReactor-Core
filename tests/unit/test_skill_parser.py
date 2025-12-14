"""Unit tests for SKILL.md parser."""

from artreactor.core.utils.skill_parser import parse_skill_md


def test_parse_basic_skill(tmp_path):
    """Test parsing a basic SKILL.md file."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""# My Test Skill

This is a test skill for demonstration purposes.

## Context Keywords

- testing
- demo
- example

## Tools

- `test_tool_1`
- `test_tool_2`

## Instructions

Use this skill when you need to test something.

## Examples

```python
test_tool_1()
```
""")

    skill = parse_skill_md(skill_file, "test-plugin")

    assert skill is not None
    assert skill.name == "My Test Skill"
    assert skill.description == "This is a test skill for demonstration purposes."
    assert skill.plugin_name == "test-plugin"
    assert "testing" in skill.context_keywords
    assert "demo" in skill.context_keywords
    assert "test_tool_1" in skill.tools
    assert "test_tool_2" in skill.tools
    assert "Use this skill when" in skill.instructions
    assert len(skill.examples) > 0


def test_parse_skill_no_sections(tmp_path):
    """Test parsing a minimal SKILL.md file."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""# Minimal Skill

Just a basic description.
""")

    skill = parse_skill_md(skill_file, "minimal-plugin")

    assert skill is not None
    assert skill.name == "Minimal Skill"
    assert skill.description == "Just a basic description."
    assert skill.context_keywords == []
    assert skill.tools == []
    assert skill.instructions == ""
    assert skill.examples == []


def test_parse_skill_nonexistent_file(tmp_path):
    """Test parsing a non-existent SKILL.md file."""
    skill_file = tmp_path / "nonexistent.md"

    skill = parse_skill_md(skill_file, "nonexistent-plugin")

    assert skill is None


def test_parse_skill_with_numbered_examples(tmp_path):
    """Test parsing SKILL.md with numbered list examples."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""# Test Skill

Description here.

## Examples

1. First example scenario
2. Second example scenario
3. Third example scenario
""")

    skill = parse_skill_md(skill_file, "test-plugin")

    assert skill is not None
    assert len(skill.examples) == 3
    assert "First example scenario" in skill.examples[0]


def test_parse_skill_context_keywords_comma_separated(tmp_path):
    """Test parsing context keywords as comma-separated list."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""# Test Skill

Description here.

## Context

git, version control, repository
""")

    skill = parse_skill_md(skill_file, "git-plugin")

    assert skill is not None
    assert len(skill.context_keywords) == 3
    assert "git" in skill.context_keywords
    assert "version control" in skill.context_keywords
    assert "repository" in skill.context_keywords


def test_parse_skill_with_yaml_frontmatter(tmp_path):
    """Test parsing SKILL.md with YAML frontmatter (Anthropic format)."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""---
name: Git Control
description: Provides Git version control operations
---

## Context Keywords

- git
- repository

## Tools

- `git_status` - Check repository status
- `git_commit` - Commit changes

## Instructions

Use this skill for Git operations.

## Examples

```python
status = git_status()
```
""")

    skill = parse_skill_md(skill_file, "git-plugin")

    assert skill is not None
    assert skill.name == "Git Control"
    assert skill.description == "Provides Git version control operations"
    assert skill.plugin_name == "git-plugin"
    assert "git" in skill.context_keywords
    assert "repository" in skill.context_keywords
    assert "git_status" in skill.tools
    assert "git_commit" in skill.tools
    assert "Use this skill for Git operations" in skill.instructions
    assert len(skill.examples) > 0


def test_parse_skill_with_yaml_frontmatter_quoted(tmp_path):
    """Test parsing SKILL.md with quoted YAML values."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""---
name: "My Skill"
description: 'A skill with quoted values'
---

## Context Keywords

- test
""")

    skill = parse_skill_md(skill_file, "test-plugin")

    assert skill is not None
    assert skill.name == "My Skill"
    assert skill.description == "A skill with quoted values"


def test_parse_skill_yaml_frontmatter_minimal(tmp_path):
    """Test parsing minimal SKILL.md with only YAML frontmatter."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""---
name: Minimal Skill
description: Just the basics
---
""")

    skill = parse_skill_md(skill_file, "minimal-plugin")

    assert skill is not None
    assert skill.name == "Minimal Skill"
    assert skill.description == "Just the basics"
    assert skill.context_keywords == []
    assert skill.tools == []
