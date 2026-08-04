"""Motion Conductor — Engine-based video generation vehicle.

Both studiolot and standalone modes share the same Engine-based execution.
The Vehicle reads video bullets, loads an Engine, and calls engine.run().

Per VEHICLE_CONTRACT.md §4d: InputFile.metadata carries {duration, fps}
from the profile YAML's parameters block.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger

from .auth import AuthenticationError, authenticate
from .cli import parse_args
from .config.profile_loader import load_profile_standalone, load_profile_studiolot
from .execution.pipeline import (
    PipelineContext,
    execute_pipeline,
    find_project_engines_dir,
)
from .input.bullet_reader import read_bullets
from .utils.logging import setup_logging


def _find_vehicle_engines_dir() -> Path:
    """Return <vehicle-root>/ENGINES/."""
    return Path(__file__).resolve().parent.parent / "ENGINES"


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
    except AuthenticationError as e:
        sys.exit(str(e))
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

    profile = load_profile_studiolot(profile_path)
    platform = profile.get("platform") or "replicate"

    input_dir = Path(args.input_dir) if args.input_dir else Path(".")
    bullets = read_bullets(input_dir)

    if args.dry_run:
        logger.info(f"DRY RUN — would process {len(bullets)} bullet(s)")
        for b in bullets:
            logger.info(f"  {b['path'].name}: {b['prompt'][:60]}...")
        return 0

    api_key = authenticate()

    project_engines = find_project_engines_dir(output_dir)
    if not project_engines:
        logger.error(
            "Engine directory not found. Expected 00_APPLICATIONS/ENGINES/ "
            "under the project root."
        )
        return 1

    ctx = PipelineContext(
        platform=platform,
        profile=profile,
        output_dir=output_dir,
        search_paths=[project_engines],
        api_key=api_key,
    )
    return execute_pipeline(ctx, bullets)


def _run_standalone(args) -> int:
    profile = load_profile_standalone()
    platform = profile.get("platform") or "replicate"

    auto_install = args.install_default_engine or os.environ.get(
        "STUDIOLOT_AUTO_INSTALL_ENGINE"
    )

    input_dir = Path("USER-FILES/04.INPUT")
    if not input_dir.is_dir():
        logger.error(f"Input directory not found: {input_dir}")
        return 1

    bullets = read_bullets(input_dir)

    output_dir = Path("USER-FILES/05.OUTPUT")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        logger.info(f"DRY RUN — would process {len(bullets)} bullet(s)")
        return 0

    api_key = authenticate()

    ctx = PipelineContext(
        platform=platform,
        profile=profile,
        output_dir=output_dir,
        search_paths=[_find_vehicle_engines_dir()],
        api_key=api_key,
    )
    vehicle_root = Path(__file__).resolve().parent.parent
    return execute_pipeline(ctx, bullets, auto_install=auto_install, vehicle_root=vehicle_root)


if __name__ == "__main__":
    sys.exit(main())
