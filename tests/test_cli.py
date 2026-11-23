"""Tests for thingiverse_publisher CLI and config loading."""

import tempfile
from pathlib import Path

from thingiverse_publisher import __version__
from thingiverse_publisher.cli import USER_AGENT, build_client, load_config


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


def test_build_client_sends_custom_user_agent() -> None:
    """build_client sets a non-default User-Agent and the bearer token."""
    headers = build_client("abc").get_httpx_client().headers
    assert headers["User-Agent"] == USER_AGENT
    assert f"thingiverse-publisher/{__version__}" == USER_AGENT
    assert headers["Authorization"] == "Bearer abc"
