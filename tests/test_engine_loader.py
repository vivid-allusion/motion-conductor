"""Tests for engine_loader module."""

import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.engine_helpers import _relative_dir
from src.engine_loader import EngineLoadContext, copy_standby_profiles, load_engine


class TestRelativeDir:
    def test_no_input_root_returns_empty(self):
        assert _relative_dir(Path("/tmp/in/sub"), None) == ""

    def test_root_dir_returns_empty(self):
        assert _relative_dir(Path("/tmp/in"), Path("/tmp/in")) == ""

    def test_nested_dir_returns_posix_relpath(self):
        assert _relative_dir(Path("/tmp/in/a/b"), Path("/tmp/in")) == "a/b"

    def test_outside_input_root_returns_empty(self):
        assert _relative_dir(Path("/other"), Path("/tmp/in")) == ""


class TestLoadEngine:
    def test_platform_none_defaults_to_replicate(self):
        with (
            patch("src.engine_loader.importlib.util.spec_from_file_location") as mock_spec,
            patch("src.engine_loader.importlib.util.module_from_spec") as mock_module,
        ):
            mock_engine_class = MagicMock()
            mock_module.return_value.Engine = mock_engine_class
            mock_spec.return_value = MagicMock()

            search_paths = [Path("/fake/ENGINES")]
            ctx = EngineLoadContext(
                platform=None,
                search_paths=search_paths,
                profile={},
                output_dir="/tmp/out",
            )
            with patch.object(Path, "is_dir", return_value=True):
                load_engine(ctx)

            mock_engine_class.assert_called_once()

    def test_raises_file_not_found_when_no_engine_dir(self):
        search_paths = [Path("/nonexistent")]
        ctx = EngineLoadContext(
            platform="replicate",
            search_paths=search_paths,
            profile={},
            output_dir="/tmp/out",
        )
        with pytest.raises(FileNotFoundError, match="Engine 'replicate' not found"):
            load_engine(ctx)


class TestCopyStandbyProfiles:
    def _make_fake_pkg(self, source_dir: Path) -> types.SimpleNamespace:
        standby = source_dir / "profiles" / "standby"
        standby.mkdir(parents=True)
        (standby / "one.yaml").write_text("a: 1\n")
        (standby / "two.yaml").write_text("b: 2\n")
        pkg = types.SimpleNamespace()
        pkg.__file__ = str(source_dir / "__init__.py")
        return pkg

    def test_seeds_into_empty_standby(self, tmp_path):
        source = tmp_path / "engine"
        pkg = self._make_fake_pkg(source)
        with patch("src.engine_loader.importlib.import_module", return_value=pkg):
            count = copy_standby_profiles("replicate", vehicle_root=tmp_path)
        assert count == 2
        dest = tmp_path / "USER-FILES" / "02.STANDBY"
        assert sorted(p.name for p in dest.glob("*.yaml")) == ["one.yaml", "two.yaml"]

    def test_skips_when_standby_not_empty(self, tmp_path):
        source = tmp_path / "engine"
        pkg = self._make_fake_pkg(source)
        dest = tmp_path / "USER-FILES" / "02.STANDBY"
        dest.mkdir(parents=True)
        (dest / "existing.yaml").write_text("keep: me\n")
        with patch("src.engine_loader.importlib.import_module", return_value=pkg):
            count = copy_standby_profiles("replicate", vehicle_root=tmp_path)
        assert count == 0
        assert not (dest / "one.yaml").exists()
        assert (dest / "existing.yaml").exists()

    def test_no_engine_package_returns_zero(self, tmp_path):
        with patch(
            "src.engine_loader.importlib.import_module",
            side_effect=ImportError("nope"),
        ):
            assert copy_standby_profiles("replicate", vehicle_root=tmp_path) == 0
