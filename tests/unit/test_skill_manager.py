"""Unit tests for SkillManager."""

import pytest
from artreactor.core.managers.skill_manager import SkillManager
from artreactor.models.plugin import AgentSkill


@pytest.fixture
def skill_manager():
    """Create a fresh SkillManager instance."""
    return SkillManager()


@pytest.fixture
def sample_skill():
    """Create a sample AgentSkill."""
    return AgentSkill(
        name="Test Skill",
        description="A test skill",
        context_keywords=["test", "demo", "example"],
        tools=["test_tool"],
        instructions="Use this for testing",
        examples=["Example 1"],
        plugin_name="test-plugin",
    )


def test_register_skill(skill_manager, sample_skill):
    """Test registering a skill."""
    skill_manager.register_skill(sample_skill)

    assert "Test Skill" in skill_manager.skills
    assert skill_manager.get_skill("Test Skill") == sample_skill


def test_get_nonexistent_skill(skill_manager):
    """Test getting a non-existent skill."""
    skill = skill_manager.get_skill("Nonexistent")
    assert skill is None


def test_get_skills_by_context(skill_manager, sample_skill):
    """Test finding skills by context."""
    skill_manager.register_skill(sample_skill)

    # Match on keyword
    matches = skill_manager.get_skills_by_context("This is a test scenario")
    assert len(matches) == 1
    assert matches[0] == sample_skill

    # No match
    matches = skill_manager.get_skills_by_context("unrelated content")
    assert len(matches) == 0


def test_get_skills_by_context_case_insensitive(skill_manager, sample_skill):
    """Test that context matching is case-insensitive."""
    skill_manager.register_skill(sample_skill)

    matches = skill_manager.get_skills_by_context("This is a TEST scenario")
    assert len(matches) == 1


def test_get_all_skills(skill_manager, sample_skill):
    """Test getting all skills."""
    skill2 = AgentSkill(
        name="Another Skill",
        description="Another test skill",
        context_keywords=["other"],
        plugin_name="other-plugin",
    )

    skill_manager.register_skill(sample_skill)
    skill_manager.register_skill(skill2)

    all_skills = skill_manager.get_all_skills()
    assert len(all_skills) == 2
    assert sample_skill in all_skills
    assert skill2 in all_skills


def test_format_skill_for_agent(skill_manager, sample_skill):
    """Test formatting a skill for agent context."""
    formatted = skill_manager.format_skill_for_agent(sample_skill)

    assert "# Skill: Test Skill" in formatted
    assert "A test skill" in formatted
    assert "**Context Keywords**" in formatted
    assert "test, demo, example" in formatted
    assert "**Available Tools**" in formatted
    assert "`test_tool`" in formatted
    assert "**Instructions**" in formatted
    assert "Use this for testing" in formatted
    assert "**Examples**" in formatted


def test_get_context_for_agent_with_context(skill_manager, sample_skill):
    """Test generating agent context with context filter."""
    skill_manager.register_skill(sample_skill)

    context = skill_manager.get_context_for_agent("test scenario")

    assert "# Available Agent Skills" in context
    assert "Test Skill" in context
    assert "A test skill" in context


def test_get_context_for_agent_no_match(skill_manager, sample_skill):
    """Test generating agent context with no matching skills."""
    skill_manager.register_skill(sample_skill)

    context = skill_manager.get_context_for_agent("completely unrelated")

    assert context == ""


def test_get_context_for_agent_all_skills(skill_manager, sample_skill):
    """Test generating agent context for all skills."""
    skill_manager.register_skill(sample_skill)

    context = skill_manager.get_context_for_agent()

    assert "# Available Agent Skills" in context
    assert "Test Skill" in context


def test_clear_skills(skill_manager, sample_skill):
    """Test clearing all skills."""
    skill_manager.register_skill(sample_skill)
    assert len(skill_manager.skills) == 1

    skill_manager.clear()
    assert len(skill_manager.skills) == 0


def test_overwrite_skill(skill_manager, sample_skill):
    """Test that registering a skill with the same name overwrites."""
    skill_manager.register_skill(sample_skill)

    # Create another skill with same name but different description
    skill2 = AgentSkill(
        name="Test Skill",
        description="Updated description",
        context_keywords=["updated"],
        plugin_name="test-plugin",
    )

    skill_manager.register_skill(skill2)

    # Should only have one skill
    assert len(skill_manager.skills) == 1
    # Should be the updated one
    retrieved = skill_manager.get_skill("Test Skill")
    assert retrieved.description == "Updated description"
