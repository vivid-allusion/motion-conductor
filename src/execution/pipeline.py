"""Engine discovery, installation, and pipeline orchestration."""

from __future__ import annotations

import importlib
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from ..engine_loader import EngineLoadContext, load_engine

ENGINE_INSTALL_MESSAGE = (
    "To install an Engine:\n"
    "  git clone https://github.com/vivid-allusion/engine-replicate.git "
    "ENGINES/engine-replicate/\n"
    "  pip install -r ENGINES/engine-replicate/requirements.txt\n\n"
    "Or install via pip:\n"
    "  pip install engine-replicate\n\n"
    "Set your API key in .env:  REPLICATE_API_TOKEN=r8_...\n"
)

SUPPORTED_PLATFORMS = ["replicate", "fal", "openrouter", "google"]


@dataclass
class PipelineContext:
    """Resolved configuration passed through the pipeline."""

    platform: str
    profile: dict[str, Any]
    output_dir: Path
    search_paths: list[Path]
    api_key: str


def find_project_engines_dir(start_dir: Path) -> Path | None:
    """Walk up from start_dir looking for 00_APPLICATIONS/ENGINES/."""
    current = start_dir.resolve()
    for _ in range(10):
        candidate = current / "00_APPLICATIONS" / "ENGINES"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def print_engine_not_found(platform: str) -> None:
    sys.stderr.write(
        f"\nError: No Engine found for platform '{platform}'.\n"
        f"Supported platforms: {', '.join(SUPPORTED_PLATFORMS)}\n\n"
        f"{ENGINE_INSTALL_MESSAGE}"
    )


def auto_install_engine(platform: str, vehicle_root: Path) -> bool:
    engines_dir = vehicle_root / "ENGINES"
    engines_dir.mkdir(exist_ok=True)
    target = engines_dir / f"engine-{platform}"

    if target.is_dir():
        logger.info(f"Engine directory already exists: {target}")
        return True

    repo_url = f"https://github.com/vivid-allusion/engine-{platform}.git"
    logger.info(f"Cloning {repo_url} -> {target}")
    result = subprocess.run(
        ["git", "clone", repo_url, str(target)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        logger.error(f"git clone failed: {result.stderr}")
        return False

    req = target / "requirements.txt"
    if req.exists():
        logger.info("Installing Engine dependencies...")
        pip_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if pip_result.returncode != 0:
            logger.error(f"pip install failed: {pip_result.stderr}")
            return False

    logger.success(f"Engine '{platform}' installed")
    return True


def build_inputs(
    bullets: list[dict[str, Any]],
    ctx: PipelineContext,
) -> list[Any]:
    """Construct InputFile objects with video metadata per VEHICLE_CONTRACT.md §4d."""
    pkg = importlib.import_module(f"engine_{ctx.platform}")
    InputFile = pkg.InputFile

    params = ctx.profile.get("parameters", {})
    fps = int(params.get("fps", 24))
    profile_duration = float(params.get("duration", 5.0))

    return [
        InputFile(
            path=b["path"],
            prompt=b["prompt"],
            reference_urls=b["reference_urls"],
            metadata={
                "duration": (
                    b["frames"] / fps if b["frames"] else profile_duration
                ),
                "fps": fps,
            },
        )
        for b in bullets
    ]


def create_engine(ctx: PipelineContext):
    """Load engine with standard on_progress logger callback."""
    engine_ctx = EngineLoadContext(
        platform=ctx.platform,
        search_paths=ctx.search_paths,
        profile=ctx.profile,
        output_dir=ctx.output_dir,
        api_key=ctx.api_key,
        on_progress=lambda msg: logger.info(msg),
    )
    return load_engine(engine_ctx)


def summarize_results(results: list[Any]) -> int:
    """Log result summary and return exit code (0=ok, 1=errors)."""
    ok = sum(1 for r in results if r.status == "ok")
    failed = sum(1 for r in results if r.status == "error")
    logger.success(f"Complete: {ok} generated, {failed} errors")

    for r in results:
        if r.status == "error":
            logger.error(f"  {r.bullet_path.name}: {r.error_msg}")

    return 1 if failed else 0


def execute_pipeline(
    ctx: PipelineContext,
    bullets: list[dict[str, Any]],
    auto_install: str | None = None,
    vehicle_root: Path | None = None,
) -> int:
    """Shared pipeline: load engine, build inputs, run, summarize results."""
    try:
        engine = create_engine(ctx)
    except FileNotFoundError:
        if auto_install and vehicle_root:
            logger.info(f"Auto-installing Engine: {auto_install}")
            if auto_install_engine(auto_install, vehicle_root):
                engine = create_engine(ctx)
            else:
                return 1
        elif auto_install:
            if auto_install_engine(auto_install, Path.cwd()):
                engine = create_engine(ctx)
            else:
                return 1
        else:
            print_engine_not_found(ctx.platform)
            logger.info(
                "Re-run with --install-default-engine=replicate "
                "to auto-install the default Engine."
            )
            return 1

    inputs = build_inputs(bullets, ctx)
    results = engine.run(inputs)
    return summarize_results(results)
