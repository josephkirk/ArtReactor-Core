"""Unit tests for URI Parser."""

import pytest

from artreactor.core.utils.uri_parser import (
    EntityURI,
    build_entity_uri,
    parse_entity_uri,
)


def test_parse_basic_uri():
    """Test parsing a basic entity URI without version."""
    uri = "entity://projectA/asset/characters/hero"
    parsed = parse_entity_uri(uri)

    assert parsed.project == "projectA"
    assert parsed.entity_type == "asset"
    assert parsed.path == "characters/hero"
    assert parsed.version is None


def test_parse_uri_with_version():
    """Test parsing an entity URI with version parameter."""
    uri = "entity://projectA/asset/characters/hero?version=v001"
    parsed = parse_entity_uri(uri)

    assert parsed.project == "projectA"
    assert parsed.entity_type == "asset"
    assert parsed.path == "characters/hero"
    assert parsed.version == "v001"


def test_parse_shot_uri():
    """Test parsing a shot entity URI."""
    uri = "entity://gameProject/shot/level1/intro?version=v002"
    parsed = parse_entity_uri(uri)

    assert parsed.project == "gameProject"
    assert parsed.entity_type == "shot"
    assert parsed.path == "level1/intro"
    assert parsed.version == "v002"


def test_parse_sequence_uri():
    """Test parsing a sequence entity URI."""
    uri = "entity://myProject/sequence/act1/scene2"
    parsed = parse_entity_uri(uri)

    assert parsed.project == "myProject"
    assert parsed.entity_type == "sequence"
    assert parsed.path == "act1/scene2"
    assert parsed.version is None


def test_parse_invalid_scheme():
    """Test parsing a URI with invalid scheme."""
    uri = "http://projectA/asset/hero"
    with pytest.raises(ValueError, match="Invalid URI scheme"):
        parse_entity_uri(uri)


def test_parse_missing_project():
    """Test parsing a URI without project."""
    uri = "entity:///asset/hero"
    with pytest.raises(ValueError, match="missing project"):
        parse_entity_uri(uri)


def test_parse_missing_entity_type():
    """Test parsing a URI without entity type."""
    uri = "entity://projectA"
    with pytest.raises(ValueError, match="missing entity type and path"):
        parse_entity_uri(uri)


def test_parse_missing_path():
    """Test parsing a URI without entity path."""
    uri = "entity://projectA/asset"
    with pytest.raises(ValueError, match="missing entity path"):
        parse_entity_uri(uri)


def test_entity_uri_to_string():
    """Test converting EntityURI back to string."""
    parsed = EntityURI(
        project="projectA",
        entity_type="asset",
        path="characters/hero",
        version="v001",
    )
    uri_str = str(parsed)

    assert uri_str == "entity://projectA/asset/characters/hero?version=v001"


def test_entity_uri_to_string_without_version():
    """Test converting EntityURI without version to string."""
    parsed = EntityURI(
        project="projectA",
        entity_type="asset",
        path="characters/hero",
    )
    uri_str = str(parsed)

    assert uri_str == "entity://projectA/asset/characters/hero"


def test_build_entity_uri():
    """Test building an entity URI from components."""
    uri = build_entity_uri(
        project="projectA",
        entity_type="asset",
        path="characters/hero",
        version="v001",
    )

    assert uri == "entity://projectA/asset/characters/hero?version=v001"


def test_build_entity_uri_without_version():
    """Test building an entity URI without version."""
    uri = build_entity_uri(
        project="projectA",
        entity_type="asset",
        path="characters/hero",
    )

    assert uri == "entity://projectA/asset/characters/hero"


def test_round_trip_parsing():
    """Test parsing and rebuilding produces the same URI."""
    original_uri = "entity://projectA/asset/characters/hero?version=v001"
    parsed = parse_entity_uri(original_uri)
    rebuilt_uri = str(parsed)

    assert rebuilt_uri == original_uri
