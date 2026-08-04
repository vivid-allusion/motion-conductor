"""Canonical Engine discovery and loading.

Per ENGINE_CONTRACT.md §7a: this is the single canonical implementation of
load_engine(). Vehicle repos vendor a snapshot copy — update here first,
then re-vendor.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from typing import Any


def _find_engine_dir(platform: str, search_paths: list[Path]) -> Path:
    """Find the engine-<platform> directory in search_paths.

    Raises:
        FileNotFoundError: No matching engine directory found.
    """
    engine_dir_name = f"engine-{platform}"
    for sp in search_paths:
        candidate = sp / engine_dir_name
        if candidate.is_dir():
            return candidate

    searched = "\n  ".join(str(sp / engine_dir_name) for sp in search_paths)
    raise FileNotFoundError(
        f"Engine '{platform}' not found. Searched:\n  {searched}"
    )


def _import_engine_package(platform: str, engine_dir: Path) -> ModuleType:
    """Import the engine_<platform> package from engine_dir.

    Tries spec-from-file-location first (for vendored copies), falls back
    to import_module (for pip-installed packages).

    Raises:
        ImportError: Package exists but cannot be imported.
    """
    root = str(engine_dir)
    if root not in sys.path:
        sys.path.insert(0, root)

    pkg_name = f"engine_{platform}"

    spec = importlib.util.spec_from_file_location(
        pkg_name, engine_dir / pkg_name / "__init__.py"
    )
    if spec is not None:
        pkg = importlib.util.module_from_spec(spec)
        sys.modules[pkg_name] = pkg
        spec.loader.exec_module(pkg)
        return pkg

    try:
        return importlib.import_module(pkg_name)
    except ImportError:
        raise ImportError(
            f"Engine package '{pkg_name}' found at {engine_dir} but cannot be "
            f"imported. Check requirements: pip install -r "
            f"{engine_dir / 'requirements.txt'}"
        ) from None


def load_engine(
    platform: str | None,
    search_paths: list[Path],
    profile: dict[str, Any],
    output_dir: str | Path,
    api_key: str | None = None,
    on_progress: Callable[[str], None] | None = None,
):
    """Find and load an Engine for the given platform.

    Args:
        platform: Engine platform name (e.g. "replicate", "fal").
                  None → defaults to "replicate" (old-profile backward compat).
        search_paths: Directories to search for ``engine-<platform>/``.
        profile: Parsed profile YAML dict.
        output_dir: Where generated files are written.
        api_key: Provider API key (or None to use env var).
        on_progress: Optional progress callback.

    Returns:
        Engine instance.

    Raises:
        FileNotFoundError: No Engine directory found in search_paths.
        ImportError: Engine package exists but cannot be imported.
    """
    resolved = platform or "replicate"
    engine_dir = _find_engine_dir(resolved, search_paths)
    pkg = _import_engine_package(resolved, engine_dir)
    return pkg.Engine(
        profile=profile,
        output_dir=output_dir,
        api_key=api_key,
        on_progress=on_progress,
    )
