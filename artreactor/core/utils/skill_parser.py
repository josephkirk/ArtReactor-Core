"""Utility for parsing SKILL.md files from plugins.

Supports Anthropic's Agent Skills format with YAML frontmatter.
"""

import logging
import re
from pathlib import Path
from typing import Optional
import yaml

from artreactor.models.plugin import AgentSkill

logger = logging.getLogger(__name__)


def parse_skill_md(skill_path: Path, plugin_name: str) -> Optional[AgentSkill]:
    """
    Parse a SKILL.md file and return an AgentSkill object.

    Supports two formats:
    1. Anthropic format with YAML frontmatter (name, description)
    2. Legacy format with markdown heading

    Args:
        skill_path: Path to the SKILL.md file
        plugin_name: Name of the plugin this skill belongs to

    Returns:
        AgentSkill object or None if parsing fails
    """
    if not skill_path.exists():
        return None

    try:
        content = skill_path.read_text(encoding="utf-8")

        # Check for YAML frontmatter (Anthropic format)
        skill_name = plugin_name
        description = ""

        # Match YAML frontmatter with optional trailing newline
        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*(?:\n|$)", content, re.DOTALL
        )
        if frontmatter_match:
            # Parse YAML frontmatter using proper YAML parser
            frontmatter_text = frontmatter_match.group(1)
            try:
                frontmatter_data = yaml.safe_load(frontmatter_text)
                if isinstance(frontmatter_data, dict):
                    skill_name = frontmatter_data.get("name", plugin_name)
                    description = frontmatter_data.get("description", "")
            except yaml.YAMLError as e:
                logger.warning(
                    f"Failed to parse YAML frontmatter for {plugin_name}: {e}"
                )
                # Fall back to legacy parsing

            # Remove frontmatter from content for further parsing
            content = content[frontmatter_match.end() :]
        else:
            # Legacy format: parse from markdown heading
            name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if name_match:
                skill_name = name_match.group(1).strip()

            # Parse description (first paragraph after title)
            desc_match = re.search(
                r"^#[^\n]+\n\n(.+?)(?:\n\n|\n#|$)", content, re.DOTALL
            )
            if desc_match:
                description = desc_match.group(1).strip()

        # Parse context keywords
        context_keywords = []
        context_section = re.search(
            r"##\s+Context(?:\s+Keywords?)?\s*\n(.+?)(?:\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if context_section:
            # Extract keywords from bullet list or comma-separated
            keywords_text = context_section.group(1).strip()
            # Try bullet list first
            bullets = re.findall(r"^\s*[-*]\s+(.+)$", keywords_text, re.MULTILINE)
            if bullets:
                context_keywords = [kw.strip() for kw in bullets]
            else:
                # Try comma-separated and filter out empty strings
                context_keywords = [
                    kw.strip() for kw in keywords_text.split(",") if kw.strip()
                ]

        # Parse tools
        tools = []
        tools_section = re.search(
            r"##\s+Tools?\s*\n(.+?)(?:\n##|\Z)", content, re.DOTALL | re.IGNORECASE
        )
        if tools_section:
            tools_text = tools_section.group(1).strip()
            # Extract from bullet list - match tool names with or without backticks
            # Match pattern: - `tool_name` or - `tool_name` - description
            bullets = re.findall(r"^\s*[-*]\s+`([^`]+)`", tools_text, re.MULTILINE)
            tools = [t.strip() for t in bullets if t.strip()]

        # Parse instructions
        instructions = ""
        instructions_section = re.search(
            r"##\s+Instructions?\s*\n(.+?)(?:\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if instructions_section:
            instructions = instructions_section.group(1).strip()

        # Parse examples
        examples = []
        examples_section = re.search(
            r"##\s+Examples?\s*\n(.+?)(?:\n##|\Z)", content, re.DOTALL | re.IGNORECASE
        )
        if examples_section:
            examples_text = examples_section.group(1).strip()
            # Split by markdown code blocks or numbered examples
            code_blocks = re.findall(r"```[\s\S]*?```", examples_text)
            if code_blocks:
                examples = code_blocks
            else:
                # Try numbered list
                numbered = re.findall(r"^\d+\.\s+(.+)$", examples_text, re.MULTILINE)
                if numbered:
                    examples = numbered

        return AgentSkill(
            name=skill_name,
            description=description,
            context_keywords=context_keywords,
            tools=tools,
            instructions=instructions,
            examples=examples,
            plugin_name=plugin_name,
        )

    except Exception as e:
        logger.error(f"Failed to parse SKILL.md for {plugin_name}: {e}")
        return None
