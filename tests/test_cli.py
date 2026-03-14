"""Tests for thingiverse_publisher CLI and config loading."""

import tempfile
from pathlib import Path

from thingiverse_publisher import __version__
from thingiverse_publisher.cli import load_config


def test_version_is_string() -> None:
    """__version__ is a non-empty string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_load_config_returns_none_for_missing_file() -> None:
    """load_config returns None when the file does not exist."""
    assert load_config("/nonexistent/path/.thingiverse_publisher.json") is None


def test_load_config_parses_valid_json() -> None:
    """load_config returns dict for a valid JSON config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"bearer_token": "abc", "username": "test"}')
        path = f.name
    try:
        result = load_config(path)
        assert result is not None
        assert result["bearer_token"] == "abc"
        assert result["username"] == "test"
    finally:
        Path(path).unlink(missing_ok=True)


def test_load_config_parses_json5_with_comments() -> None:
    """load_config parses JSON5 with comments."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(
            """{
                // optional comment
                "bearer_token": "xyz",
                "username": "someone"
            }"""
        )
        path = f.name
    try:
        result = load_config(path)
        assert result is not None
        assert result["bearer_token"] == "xyz"
        assert result["username"] == "someone"
    finally:
        Path(path).unlink(missing_ok=True)
