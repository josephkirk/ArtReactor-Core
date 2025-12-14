"""Manager for agent skills from plugins."""

import logging
from typing import Dict, List, Optional

from artreactor.models.plugin import AgentSkill

logger = logging.getLogger(__name__)


class SkillManager:
    """Manages agent skills loaded from plugins."""

    def __init__(self):
        self.skills: Dict[str, AgentSkill] = {}

    def register_skill(self, skill: AgentSkill):
        """
        Register a new skill.

        Args:
            skill: The skill to register
        """
        if skill.name in self.skills:
            logger.warning(f"Skill {skill.name} already registered, overwriting")

        self.skills[skill.name] = skill
        logger.info(f"Registered skill: {skill.name} (plugin: {skill.plugin_name})")

    def get_skill(self, name: str) -> Optional[AgentSkill]:
        """
        Get a skill by name.

        Args:
            name: Name of the skill

        Returns:
            The skill if found, None otherwise
        """
        return self.skills.get(name)

    def get_skills_by_context(self, context: str) -> List[AgentSkill]:
        """
        Find skills that match the given context.

        Args:
            context: Context string to match against skill keywords

        Returns:
            List of matching skills
        """
        context_lower = context.lower()
        matching_skills = []

        for skill in self.skills.values():
            # Check if any keyword matches the context
            for keyword in skill.context_keywords:
                if keyword.lower() in context_lower:
                    matching_skills.append(skill)
                    break

        return matching_skills

    def get_all_skills(self) -> List[AgentSkill]:
        """
        Get all registered skills.

        Returns:
            List of all skills
        """
        return list(self.skills.values())

    def format_skill_for_agent(self, skill: AgentSkill) -> str:
        """
        Format a skill definition for inclusion in agent context.

        Args:
            skill: The skill to format

        Returns:
            Formatted skill string
        """
        parts = [
            f"# Skill: {skill.name}",
            f"\n{skill.description}\n",
        ]

        if skill.context_keywords:
            parts.append(f"**Context Keywords**: {', '.join(skill.context_keywords)}")

        if skill.tools:
            parts.append("\n**Available Tools**:")
            for tool in skill.tools:
                parts.append(f"- `{tool}`")

        if skill.instructions:
            parts.append(f"\n**Instructions**:\n{skill.instructions}")

        if skill.examples:
            parts.append("\n**Examples**:")
            for i, example in enumerate(skill.examples, 1):
                # Preserve formatting for multi-line examples
                if "\n" in example:
                    parts.append(f"\n{i}.\n{example}")
                else:
                    parts.append(f"\n{i}. {example}")

        return "\n".join(parts)

    def get_context_for_agent(self, context: Optional[str] = None) -> str:
        """
        Generate skill context string for an agent.

        Args:
            context: Optional context to filter skills

        Returns:
            Formatted string with relevant skills
        """
        if context:
            skills = self.get_skills_by_context(context)
            if not skills:
                return ""
        else:
            skills = self.get_all_skills()

        if not skills:
            return ""

        parts = [
            "# Available Agent Skills",
            "\nThe following skills are available from loaded plugins:\n",
        ]

        for skill in skills:
            parts.append(self.format_skill_for_agent(skill))
            parts.append("\n---\n")

        return "\n".join(parts)

    def clear(self):
        """Clear all registered skills."""
        self.skills.clear()
