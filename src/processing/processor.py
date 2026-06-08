"""Video generation processor with batch handling."""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


def _record_adjustment(
    adjustment_info: Dict[str, Any] | None,
    job_name: str,
    profile_name: str,
    all_adjustments: List[Dict[str, Any]],
) -> None:
    """Record duration adjustment info if present."""
    if adjustment_info and adjustment_info.get("reason"):
        all_adjustments.append(
            {
                "prompt_file": job_name,
                "profile": profile_name,
                **adjustment_info,
            }
        )
from datetime import datetime
from loguru import logger
from rich.progress import Progress

from ..api.client import ReplicateClient
from .input_discovery import discover_markdown_jobs, parse_markdown_job
from .profile_loader import load_active_profiles
from .cost_calculator import calculate_cost_from_params
from .output_generator import save_generation_files
from ..utils.filename_utils import generate_video_filename
from .duration_handler import (
    process_duration,
    get_duration_parameter_name,
    should_include_fps,
)
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from ..models.triplet import MarkdownJob
from ..models.video_processing import VideoGenerationRequest
from .generation_logger import log_generation_start, log_generation_complete
from ..utils.path_validator import validate_custom_paths


def _enforce_single_profile(active_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate exactly one profile is active and return it."""
    if len(active_profiles) == 0:
        logger.error("No profiles found in 03.PROFILES/")
        raise FileNotFoundError(
            "No profiles found. Place exactly one profile YAML file in 03.PROFILES/"
        )
    if len(active_profiles) > 1:
        profile_names = [p["name"] for p in active_profiles]
        logger.error(f"Multiple profiles found: {', '.join(profile_names)}")
        raise Exception(
            f"Multiple profiles found in 03.PROFILES/: {', '.join(profile_names)}. "
            "Keep only one profile in the directory."
        )
    return active_profiles[0]


def _process_jobs(
    client: ReplicateClient,
    jobs: List[MarkdownJob],
    profile: Dict[str, Any],
    output_dir: Path,
    progress: Optional[Progress] = None,
) -> Tuple[int, float, List[Dict[str, Any]]]:
    """Process all video generations for a single profile."""
    total = len(jobs)
    success_count = 0
    total_cost = 0.0
    all_adjustments = []

    task_id = None
    if progress:
        task_id = progress.add_task("Generating videos", total=total)

    for job in jobs:
        video_cost, adjustment_info = _process_single_video(
            client, job, profile, output_dir
        )

        _record_adjustment(adjustment_info, job.markdown_file.name, profile["name"], all_adjustments)

        success_count += 1
        total_cost += video_cost

        if progress and task_id is not None:
            progress.advance(task_id)

    return success_count, total_cost, all_adjustments


def process_batch(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process markdown job files with a single profile for video generation.

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results

    Raises:
        Exception: On any processing failure (fail-fast)
    """
    # 1. Load and enforce single profile
    active_profiles = load_active_profiles(context.profiles_dir)
    logger.info(f"Loaded {len(active_profiles)} profile(s)")
    profile = _enforce_single_profile(active_profiles)
    logger.info(f"Using profile: {profile['name']}")

    # 2. Validate custom paths for the profile
    custom_input = profile.get("custom_input_path")
    custom_output = profile.get("custom_output_path")
    if custom_input or custom_output:
        validate_custom_paths(
            Path(custom_input) if custom_input else None,
            Path(custom_output) if custom_output else None,
        )

    # 3. Discover markdown jobs
    input_path = Path(custom_input) if custom_input else context.input_dir
    markdown_files = discover_markdown_jobs(input_path)
    jobs = [parse_markdown_job(md_file) for md_file in markdown_files]
    logger.info(f"Discovered {len(jobs)} markdown jobs")

    if not jobs:
        logger.warning("No markdown jobs found")
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "cost": 0.0,
            "output_dir": context.output_dir,
            "adjustments": [],
        }

    # 4. Determine output directory
    run_timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    if custom_output:
        profile_suffix = (
            str(profile["name"]).strip().replace("/", "-").replace(" ", "_")
        )
        output_dir = Path(custom_output) / f"{run_timestamp}_{profile_suffix}"
    else:
        output_dir = context.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # 5. Process jobs sequentially
    total = len(jobs)
    success_count, total_cost, all_adjustments = _process_jobs(
        context.client, jobs, profile, output_dir, context.progress
    )

    return {
        "total": total,
        "success": success_count,
        "failed": total - success_count,
        "cost": total_cost,
        "output_dir": output_dir,
        "adjustments": all_adjustments,
    }


def _apply_prompt_modifications(prompt: str, profile: Dict[str, Any]) -> str:
    """
    Apply prefix and suffix modifications to prompt based on profile configuration.

    Args:
        prompt: Original prompt text
        profile: Profile configuration dictionary

    Returns:
        Modified prompt with prefix/suffix applied

    Raises:
        ValueError: If final prompt is empty after modifications
    """
    prompt = prompt.strip()

    prefix = profile.get("prompt_prefix")
    if prefix and prefix.strip():
        prompt = f"{prefix.strip()} {prompt}" if prompt else prefix.strip()

    suffix = profile.get("prompt_suffix")
    if suffix and suffix.strip():
        prompt = f"{prompt} {suffix.strip()}" if prompt else suffix.strip()

    prompt = " ".join(prompt.split())
    if not prompt:
        raise ValueError("Final prompt is empty after applying modifications")

    return prompt


def _process_single_video(
    client: ReplicateClient, job: MarkdownJob, profile: Dict[str, Any], run_dir: Path
) -> Tuple[float, Dict[str, Any]]:
    """
    Process a single video generation from markdown job.

    Args:
        client: Replicate API client
        job: MarkdownJob with parsed data
        profile: Profile configuration
        run_dir: Output directory

    Returns:
        Tuple of (cost, adjustment_info)

    Raises:
        Exception: On generation failure
    """
    prompt = job.prompt
    image_url = job.image_url
    num_frames = job.num_frames

    original_prompt = prompt
    prompt = _apply_prompt_modifications(prompt, profile)

    processing_name = job.markdown_file.stem
    logger.info(f"Processing: {processing_name}")

    try:
        params, adjustment_info = _prepare_generation_params(profile, num_frames)

        log_generation_start(
            processing_name, profile, prompt, image_url, num_frames, params
        )

        gen_request = VideoGenerationRequest(
            client=client,
            profile=profile,
            image_url=image_url,
            prompt=prompt,
            params=params,
            output_dir=run_dir,
            markdown_file=job.markdown_file,
        )
        video_url, video_path = _generate_and_download_video(gen_request)

        video_cost = calculate_cost_from_params(profile, params, num_frames)

        context = GenerationContext.from_video_result(
            job=job,
            output_dir=run_dir,
            profile=profile,
            params=params,
            prompt=original_prompt,
            video_url=video_url,
            video_path=video_path,
            cost=video_cost,
            adjustment_info=adjustment_info,
        )

        video_filename_stem = video_path.stem
        save_generation_files(context, video_filename_stem)

        log_generation_complete(video_path, video_cost)

        return video_cost, adjustment_info

    except Exception as e:
        logger.error(f"Failed: {job.markdown_file.name} + {profile['name']}: {e}")
        raise


def _prepare_generation_params(
    profile: Dict[str, Any], num_frames: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Prepare API parameters with duration handling.

    Returns:
        Tuple of (params, adjustment_info)
    """
    params = profile["parameters"].copy()

    adjusted_duration, was_adjusted, adjustment_info = process_duration(
        num_frames, profile
    )

    param_name = get_duration_parameter_name(profile)
    params[param_name] = adjusted_duration

    if should_include_fps(profile):
        params["fps"] = profile["duration_config"]["fps"]

    return params, adjustment_info


def _generate_and_download_video(request: VideoGenerationRequest) -> Tuple[str, Path]:
    """
    Generate video and download it.

    Args:
        request: VideoGenerationRequest with all required parameters

    Returns:
        Tuple of (video_url, video_path)
    """
    from .video_downloader import download_video

    video_url = request.client.generate_video(
        model_name=request.profile["model_id"],
        image_url=request.image_url,
        prompt=request.prompt,
        params=request.params,
        image_url_param=request.profile.get("image_url_param", "image"),
    )

    if not video_url:
        raise Exception(f"Failed to generate video for {request.markdown_file.name}")

    video_filename = generate_video_filename(request.markdown_file.name)
    video_path = request.output_dir / video_filename
    download_video(video_url, video_path)

    return video_url, video_path
