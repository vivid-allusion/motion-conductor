"""Motion Conductor — migrated to Engine interface.

Both studiolot and standalone modes share the same Engine-based execution.
The Vehicle reads video bullets, loads an Engine, and calls engine.run().

Per VEHICLE_CONTRACT.md §4d: InputFile.metadata carries {duration, fps}
from the profile YAML's parameters block.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Any

from loguru import logger

from .auth import authenticate
from .cli import parse_args
from .engine_loader import load_engine
from .utils.logging import setup_logging

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

_FRAMES_RE = re.compile(r"^frames:\s*(\d+)", re.IGNORECASE)


def _read_bullets(input_dir: Path) -> list[dict[str, Any]]:
    """Read bullet .md files from input_dir, extract prompt, ref URLs, frames."""
    md_files = sorted(input_dir.rglob("*.md"))
    bullets: list[dict[str, Any]] = []
    for md_path in md_files:
        content = md_path.read_text(encoding="utf-8")
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

        prompt = ""
        if lines:
            l0 = lines[0]
            if not l0.startswith("!["):
                prompt = l0

        urls: list[str] = []
        for ln in lines:
            m = re.search(r"!\[.*?\]\((https?://[^)]+)\)", ln)
            if m:
                urls.append(m.group(1))

        frames = None
        for ln in lines:
            m = _FRAMES_RE.match(ln)
            if m:
                frames = int(m.group(1))
                break

        bullets.append({
            "path": md_path,
            "prompt": prompt,
            "reference_urls": urls,
            "frames": frames,
        })

    if not bullets:
        logger.error(f"No .md files found in {input_dir}")
        raise FileNotFoundError(f"No .md files found in {input_dir}")

    logger.info(f"Discovered {len(bullets)} bullet(s) in {input_dir}")
    return bullets


def _load_profile_standalone() -> dict[str, Any]:
    """Load profile from USER-FILES for standalone mode, normalize format."""
    profiles_dir = Path("USER-FILES/03.PROFILES")
    yamls = sorted(profiles_dir.glob("*.yaml")) + sorted(profiles_dir.glob("*.yml"))
    if not yamls:
        standby = Path("USER-FILES/02.STANDBY")
        yamls = sorted(standby.glob("*.yaml")) + sorted(standby.glob("*.yml"))
    if not yamls:
        raise FileNotFoundError(
            "No profile found in USER-FILES/03.PROFILES/ or USER-FILES/02.STANDBY/"
        )

    data = yaml.safe_load(yamls[0].read_text(encoding="utf-8")) or {}

    if "Model" in data and "endpoint" not in data:
        data["endpoint"] = data["Model"].get("endpoint", "")

    if "platform" not in data:
        data["platform"] = "replicate"

    if "media_type" not in data:
        data["media_type"] = "video"

    if "duration_config" in data and "parameters" not in data:
        dc = data.get("duration_config", {})
        if dc:
            params = {
                "fps": dc.get("fps", 24),
            }
            data["parameters"] = params
    elif "parameters" not in data:
        data["parameters"] = {}

    params = data.get("parameters", {})
    if "fps" not in params:
        params["fps"] = 24

    data["profile_name"] = yamls[0].stem
    return data


def _load_profile_studiolot(profile_path: Path) -> dict[str, Any]:
    """Load profile YAML from --profile flag."""
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    data["profile_name"] = profile_path.stem
    return data


def _find_project_engines_dir(start_dir: Path) -> Path | None:
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


def _find_vehicle_engines_dir() -> Path:
    """Return <vehicle-root>/ENGINES/."""
    return Path(__file__).resolve().parent.parent / "ENGINES"


def _print_engine_not_found(platform: str):
    sys.stderr.write(
        f"\nError: No Engine found for platform '{platform}'.\n"
        f"Supported platforms: {', '.join(SUPPORTED_PLATFORMS)}\n\n"
        f"{ENGINE_INSTALL_MESSAGE}"
    )


def _auto_install_engine(platform: str) -> bool:
    vehicle_root = Path(__file__).resolve().parent.parent
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
    )
    if result.returncode != 0:
        logger.error(f"git clone failed: {result.stderr}")
        return False

    req = target / "requirements.txt"
    if req.exists():
        logger.info("Installing Engine dependencies...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
            check=False,
        )

    logger.success(f"Engine '{platform}' installed")
    return True


def _build_inputs(
    bullets: list[dict[str, Any]],
    profile: dict[str, Any],
    platform: str,
) -> list[Any]:
    """Construct InputFile objects with video metadata per VEHICLE_CONTRACT.md §4d."""
    pkg = importlib.import_module(f"engine_{platform}")
    InputFile = pkg.InputFile

    params = profile.get("parameters", {})
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


def main():
    args = parse_args()
    is_studiolot = bool(args.profile or args.input_dir or args.output_dir)
    setup_logging(verbose=True, debug=args.debug)

    logger.info("=" * 60)
    logger.info("Motion Conductor — Video Generation")
    logger.info("=" * 60)

    try:
        if is_studiolot:
            return _run_studiolot(args)
        else:
            return _run_standalone(args)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


def _run_studiolot(args) -> int:
    if not args.output_dir:
        logger.error("--output_dir is required in studiolot mode")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    profile_path = Path(args.profile) if args.profile else None
    if not profile_path:
        logger.error("--profile is required in studiolot mode")
        return 1

    profile = _load_profile_studiolot(profile_path)
    platform = profile.get("platform") or "replicate"

    input_dir = Path(args.input_dir) if args.input_dir else Path(".")

    bullets = _read_bullets(input_dir)

    if args.dry_run:
        logger.info(f"DRY RUN — would process {len(bullets)} bullet(s)")
        for b in bullets:
            logger.info(f"  {b['path'].name}: {b['prompt'][:60]}...")
        return 0

    api_key = authenticate()

    project_engines = _find_project_engines_dir(output_dir)
    if not project_engines:
        logger.error(
            "Engine directory not found. Expected 00_APPLICATIONS/ENGINES/ "
            "under the project root."
        )
        return 1

    engine = load_engine(
        platform=platform,
        search_paths=[project_engines],
        profile=profile,
        output_dir=output_dir,
        api_key=api_key,
        on_progress=lambda msg: logger.info(msg),
    )

    inputs = _build_inputs(bullets, profile, platform)
    results = engine.run(inputs)

    ok = sum(1 for r in results if r.status == "ok")
    failed = sum(1 for r in results if r.status == "error")
    logger.success(f"Complete: {ok} generated, {failed} errors")

    for r in results:
        if r.status == "error":
            logger.error(f"  {r.bullet_path.name}: {r.error_msg}")

    return 1 if failed else 0


def _run_standalone(args) -> int:
    profile = _load_profile_standalone()
    platform = profile.get("platform") or "replicate"

    auto_install = args.install_default_engine or os.environ.get(
        "STUDIOLOT_AUTO_INSTALL_ENGINE"
    )

    input_dir = Path("USER-FILES/04.INPUT")
    if not input_dir.is_dir():
        logger.error(f"Input directory not found: {input_dir}")
        return 1

    bullets = _read_bullets(input_dir)

    output_dir = Path("USER-FILES/05.OUTPUT")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        logger.info(f"DRY RUN — would process {len(bullets)} bullet(s)")
        return 0

    api_key = authenticate()

    search_paths = [_find_vehicle_engines_dir()]

    try:
        engine = load_engine(
            platform=platform,
            search_paths=search_paths,
            profile=profile,
            output_dir=output_dir,
            api_key=api_key,
            on_progress=lambda msg: logger.info(msg),
        )
    except FileNotFoundError:
        if auto_install:
            logger.info(f"Auto-installing Engine: {auto_install}")
            if _auto_install_engine(auto_install):
                engine = load_engine(
                    platform=platform,
                    search_paths=search_paths,
                    profile=profile,
                    output_dir=output_dir,
                    api_key=api_key,
                    on_progress=lambda msg: logger.info(msg),
                )
            else:
                return 1
        else:
            _print_engine_not_found(platform)
            logger.info(
                "Re-run with --install-default-engine=replicate "
                "to auto-install the default Engine."
            )
            return 1

    inputs = _build_inputs(bullets, profile, platform)
    results = engine.run(inputs)

    ok = sum(1 for r in results if r.status == "ok")
    failed = sum(1 for r in results if r.status == "error")
    logger.success(f"Complete: {ok} generated, {failed} errors")

    for r in results:
        if r.status == "error":
            logger.error(f"  {r.bullet_path.name}: {r.error_msg}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
