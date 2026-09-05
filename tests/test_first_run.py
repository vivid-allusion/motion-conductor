"""Tests for first-run behavior: engines seed 02.STANDBY only, never 03.PROFILES."""

from unittest.mock import patch

from src.processing.first_run import handle_first_run


def test_first_run_never_auto_populates_active_profiles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    engines = tmp_path / "ENGINES"
    (engines / "engine-replicate").mkdir(parents=True)

    standby = tmp_path / "USER-FILES" / "02.STANDBY"
    standby.mkdir(parents=True)
    (standby / "some-profile.yaml").write_text("platform: replicate\n")

    with (
        patch("src.processing.first_run.load_engine_or_install") as mock_load,
        patch("src.processing.first_run.print_engine_not_found"),
    ):
        result = handle_first_run("replicate", [engines], dry_run=False, auto_install=None)

    assert result == ("replicate", None)
    mock_load.assert_called_once()

    active = tmp_path / "USER-FILES" / "03.PROFILES"
    active_yamls = (
        sorted(active.glob("*.yaml")) + sorted(active.glob("*.yml")) if active.is_dir() else []
    )
    assert not active_yamls
