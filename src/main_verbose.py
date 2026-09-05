"""Motion Conductor — Engine-based video generation vehicle.

Both studiolot and standalone modes share the same Engine-based execution.
The Vehicle reads video bullets, loads an Engine, and calls engine.run().

Per VEHICLE_CONTRACT.md §4d: InputFile.metadata carries {duration, fps}
from the profile YAML's parameters block.
"""

import os
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from .auth import get_api_key, get_api_key_interactive
from .cli import parse_args
from .constants import DEFAULT_PLATFORM, __version__
from .datatypes import Bullet
from .engine_helpers import (
    build_inputs,
    find_project_engines_dir,
    make_engine_ctx,
)
from .engine_loader import load_engine
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    PreflightExit,
    ValidationError,
)
from .processing.bullet_parser import read_bullets
from .processing.first_run import handle_first_run
from .processing.profiles import (
    load_profile_standalone,
    load_profile_studiolot,
)
from .utils.logging import setup_logging, start_output_capture, write_run_logs
from .utils.path_resolver import (
    create_timestamped_output_path,
    resolve_input_path,
    resolve_output_base_path,
)

# ── CLI / orchestration helpers ────────────────────────────────────────────────


def _print_profile_guidance() -> None:
    """Pretty guidance for activating a profile after the first-run wizard."""
    from rich.console import Console
    from rich.text import Text

    root = Path(__file__).resolve().parent.parent
    standby = root / "USER-FILES" / "02.STANDBY"
    active = root / "USER-FILES" / "03.PROFILES"

    body = Text()
    body.append("Thanks for supplying your API key!\n", style="bold green")
    body.append("To make the script operational:\n", style="bold")
    body.append("  1. Pick a profile YAML from:\n", style="dim")
    body.append(f"     {standby}/\n", style="cyan")
    body.append("  2. Copy it to:\n", style="dim")
    body.append(f"     {active}/\n", style="cyan")
    body.append("  3. Re-run the script\n", style="dim")

    Console().print(body)



def _apply_cli_overrides(profile: dict[str, Any], args: Any) -> dict[str, Any]:
    """Return a copy of profile with CLI flags merged into parameters."""
    params = dict(profile.get("parameters", {}))
    if not args.save_payloads:
        params["save_payloads"] = False
    return {**profile, "parameters": params}


def _bullet_duration(bullet: Bullet, profile: dict[str, Any]) -> float:
    """Duration for a bullet: numeric `duration:` verbatim, else frames via
    fps, else profile default. Token durations (auto, -1) fall back to the
    profile default for cost estimation only."""
    params = profile.get("parameters", {})
    fps = float(params.get("fps", 24))
    profile_duration = float(params.get("duration", 5.0))
    raw = bullet.get("duration")
    if isinstance(raw, (int, float)) and raw > 0:
        return float(raw)
    if bullet["frames"]:
        return bullet["frames"] / fps
    return profile_duration


def _handle_preflight_checks(
    args: Any, bullets: list[Bullet], profile: dict[str, Any]
) -> None:
    if args.cost_estimation:
        cost_per_second = float(profile.get("pricing", {}).get("cost_per_second", 0.0))
        total = sum(_bullet_duration(b, profile) * cost_per_second for b in bullets)
        logger.info(
            f"Estimated cost: {len(bullets)} bullet(s), "
            f"{sum(_bullet_duration(b, profile) for b in bullets):.1f}s total "
            f"x ${cost_per_second:.4f}/s = ${total:.2f}"
        )
        raise PreflightExit(0)
    if args.dry_run:
        logger.info(f"DRY RUN -- would process {len(bullets)} bullet file(s)")
        raise PreflightExit(0)


def _report_results(results: list[Any]) -> int:
    """Summarise engine.run() results and return exit code."""
    ok = sum(1 for r in results if r.status == "ok")
    failed = sum(1 for r in results if r.status == "error")
    sys.stderr.write(f"Complete: {ok} generated, {failed} errors\n")
    for r in results:
        if r.status == "error":
            logger.error(f"  {r.source_path.name}: {r.error_msg}")
    return 1 if failed else 0


def _execute_pipeline(
    bullets: list[Bullet],
    engine: Any,
    platform: str,
    profile: dict[str, Any],
    output_dir: Path,
    input_root: Path | None = None,
) -> int:
    """Run the core generation pipeline: build inputs → run → report → log."""
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
    )

    inputs = build_inputs(bullets, platform, input_root, profile)
    total = len(inputs)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as bar:
        task = bar.add_task("Processing...", total=total)

        def on_progress(msg: Any) -> None:
            text = msg.message if hasattr(msg, "message") else str(msg)
            bar.update(task, description=text)
            current = getattr(msg, "current", 0)
            if current:
                bar.update(task, completed=current)
            if getattr(msg, "level", "") == "error":
                logger.error(text)
            payload = getattr(msg, "api_payload", None)
            if payload is not None:
                logger.info(f"Payload: {payload}")

        original = engine._on_progress
        engine._on_progress = on_progress
        try:
            results = engine.run(inputs)
        finally:
            engine._on_progress = original

    exit_code = _report_results(results)
    generated = [
        r.path
        for r in results
        if r.status == "ok" and getattr(r, "path", None)
    ]
    write_run_logs(generated, output_dir)
    return exit_code


def _resolve_engine_for_studiolot(
    output_dir: Path,
    platform: str,
    profile: dict[str, Any],
    api_key: str | None,
) -> Any:
    project_engines = find_project_engines_dir(output_dir)
    if not project_engines:
        raise FileNotFoundError(
            "Engine directory not found. Expected 00_APPLICATIONS/ENGINES/ "
            "under the project root."
        )
    return load_engine(
        make_engine_ctx(platform, [project_engines], profile, output_dir, api_key)
    )


# ── entry point ────────────────────────────────────────────────────────────────


def main() -> int:
    args = parse_args()
    is_studiolot = bool(args.profile or args.input_dir or args.output_dir)
    start_output_capture()
    setup_logging(debug=args.debug, verbose=args.verbose)

    logger.debug("=" * 60)
    logger.debug(f"Motion Conductor — Video Generation v{__version__}")
    logger.debug("=" * 60)

    try:
        if is_studiolot:
            return _run_studiolot(args)
        else:
            return _run_standalone(args)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except PreflightExit as e:
        return e.exit_code
    except (AuthenticationError, ConfigurationError, ValidationError) as e:
        logger.error(f"Error: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


# ── run modes ──────────────────────────────────────────────────────────────────


def _run_studiolot(args) -> int:
    if not args.output_dir:
        raise ConfigurationError("--output_dir is required in studiolot mode")
    if not args.profile:
        raise ConfigurationError("--profile is required in studiolot mode")

    output_dir = Path(args.output_dir)
    profile_path = Path(args.profile)

    profile = load_profile_studiolot(profile_path)
    profile = _apply_cli_overrides(profile, args)
    platform = args.platform or profile.get("platform") or DEFAULT_PLATFORM
    profile["platform"] = platform

    input_dir = Path(args.input_dir) if args.input_dir else Path(".")

    bullets = read_bullets(
        input_dir,
        dry_run=args.dry_run,
        declared_slots=profile.get("slots"),
        primary_slot=profile.get("image_url_param") or "image",
    )
    if not bullets:
        if any(input_dir.rglob("*.md")):
            raise ValidationError(
                f"All bullets in {input_dir} were rejected — see errors above"
            )
        raise FileNotFoundError(f"No .md files found in {input_dir}")
    _handle_preflight_checks(args, bullets, profile)

    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = get_api_key(platform)
    engine = _resolve_engine_for_studiolot(output_dir, platform, profile, api_key)

    return _execute_pipeline(bullets, engine, platform, profile, output_dir, input_dir)


def _run_standalone(args) -> int:
    search_paths = [Path(__file__).resolve().parent.parent / "ENGINES"]
    platform = DEFAULT_PLATFORM

    auto_install = args.install_default_engine or os.environ.get(
        "STUDIOLOT_AUTO_INSTALL_ENGINE"
    )

    result = handle_first_run(platform, search_paths, args.dry_run, auto_install)
    if result is None:
        return 1
    platform, api_key = result

    try:
        profile = load_profile_standalone()
        platform = profile.get("platform") or platform
    except ConfigurationError:
        _print_profile_guidance()
        return 0

    profile = _apply_cli_overrides(profile, args)

    # ── check inputs before creating output dir ──────────────────────────────

    input_path, _ = resolve_input_path(profile)
    bullets = read_bullets(
        input_path,
        dry_run=args.dry_run,
        declared_slots=profile.get("slots"),
        primary_slot=profile.get("image_url_param") or "image",
    )
    _handle_preflight_checks(args, bullets, profile)

    if not bullets:
        if any(input_path.rglob("*.md")):
            logger.error(
                f"All bullets in {input_path} were rejected — nothing to process"
            )
            return 1
        logger.warning(
            f"No .md files to process. Add .md files to {input_path} and re-run."
        )
        return 0

    # ── output directory (only created when generation is confirmed) ────────

    output_base = resolve_output_base_path(profile)
    output_dir = create_timestamped_output_path(output_base)

    # ── API key (engine existed but wizard was skipped) ──────────────────────

    if not args.dry_run and api_key is None:
        try:
            api_key = get_api_key(platform)
        except AuthenticationError:
            if sys.stdin.isatty():
                platform, api_key = get_api_key_interactive()
                profile["platform"] = platform
            else:
                raise

    # ── engine with proper profile ───────────────────────────────────────────

    engine = load_engine(
        make_engine_ctx(platform, search_paths, profile, output_dir, api_key)
    )

    return _execute_pipeline(bullets, engine, platform, profile, output_dir, input_path)


if __name__ == "__main__":
    sys.exit(main())
