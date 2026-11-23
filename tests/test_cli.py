"""Tests for thingiverse_publisher CLI and config loading."""

import json
import tempfile
from pathlib import Path

import httpx
import pytest
from thingiverse.models.post_things_body_license import PostThingsBodyLicense
from thingiverse_publisher import __version__, cli
from thingiverse_publisher.cli import (
    USER_AGENT,
    VALID_LICENSES,
    InvalidLicenseError,
    _thing_to_patch_body,
    _thing_to_post_body,
    build_client,
    load_config,
    normalize_license,
)


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


def test_valid_licenses_match_api_codes() -> None:
    """The valid license codes are the ones the Thingiverse API accepts."""
    assert set(VALID_LICENSES) == {
        "bsd", "cc", "cc-sa", "cc-nd", "cc-nc-sa", "cc-nc-nd", "pd0", "gpl", "lgpl",
    }  # fmt: skip


@pytest.mark.parametrize("code", VALID_LICENSES)
def test_post_body_accepts_valid_license(code: str) -> None:
    body = _thing_to_post_body({"name": "x", "license": code})
    assert body.license_.value == code


def test_post_body_missing_license_defaults_to_cc() -> None:
    assert _thing_to_post_body({"name": "x"}).license_ == PostThingsBodyLicense.CC


@pytest.mark.parametrize("bad", ["BSD-3", "gpl3", "", 5])
def test_post_body_rejects_invalid_license(bad: object) -> None:
    with pytest.raises(InvalidLicenseError) as exc:
        _thing_to_post_body({"name": "x", "license": bad})
    for code in VALID_LICENSES:
        assert code in str(exc.value)


@pytest.mark.parametrize("code", VALID_LICENSES)
def test_patch_body_accepts_valid_license(code: str) -> None:
    body = _thing_to_patch_body({"name": "x", "license": code})
    assert body.license_ == code


def test_patch_body_missing_license_is_omitted() -> None:
    body = _thing_to_patch_body({"name": "x"})
    assert "license" not in body.to_dict()


@pytest.mark.parametrize("bad", ["BSD-3", "gpl3", ""])
def test_patch_body_rejects_invalid_license(bad: str) -> None:
    with pytest.raises(InvalidLicenseError) as exc:
        _thing_to_patch_body({"name": "x", "license": bad})
    assert "bsd" in str(exc.value)


def test_license_display_names_and_case() -> None:
    assert normalize_license("BSD License") == PostThingsBodyLicense.BSD
    assert normalize_license(" GPL ") == PostThingsBodyLicense.GPL
    assert normalize_license("Creative Commons - Attribution") == PostThingsBodyLicense.CC
    assert _thing_to_patch_body({"license": "BSD License"}).license_ == "bsd"


def _run_main(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, thing: dict) -> Path:
    (tmp_path / "README.md").write_text("readme")
    (tmp_path / "print-instructions.md").write_text("instr")
    cfg = tmp_path / ".thingiverse_publisher.json"
    cfg.write_text(json.dumps({"thing": thing}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("sys.argv", ["thingiverse-publisher", "-b", "tok", "-u", "me"])
    monkeypatch.setattr(cli, "config", {})
    monkeypatch.setattr(cli, "local_config", {})
    return cfg


def test_main_exits_nonzero_and_saves_id_on_api_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cfg = _run_main(monkeypatch, tmp_path, {"name": "x"})

    def fail() -> None:
        cli.config["thing"]["id"] = 42  # created before the failure
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(cli, "create_or_update_thing", fail)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert json.loads(cfg.read_text())["thing"] == {"name": "x", "id": 42}


def test_main_exits_nonzero_on_invalid_license_without_api_calls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _run_main(monkeypatch, tmp_path, {"name": "x", "license": "BSD-3"})
    monkeypatch.setattr(cli, "create_or_update_thing", lambda: pytest.fail("must not call the API"))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1


def test_main_succeeds_with_exit_zero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = _run_main(monkeypatch, tmp_path, {"name": "x", "license": "bsd"})
    monkeypatch.setattr(cli, "create_or_update_thing", lambda: None)
    cli.main()
    assert json.loads(cfg.read_text())["thing"] == {"name": "x", "license": "bsd"}
