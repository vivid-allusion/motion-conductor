"""Hybrid video processor using BOTH alive-progress AND Rich for maximum impact."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from loguru import logger

from ..api.async_client_enhanced import AsyncReplicateClientEnhanced
from ..utils.verbose_output import log_stage_emoji
from ..utils.hybrid_progress import HybridVideoProgress, create_hybrid_api_callback
from ..utils.filename_utils import generate_video_filename
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from ..models.triplet import MarkdownJob
from ..models.video_processing import VideoProcessingContext, APIClientConfig
from .cost_calculator import calculate_cost_from_params
from .input_discovery import discover_markdown_jobs, parse_markdown_job
from .output_generator import save_generation_files
from .profile_loader import load_active_profiles
from .video_downloader import download_video
from .processor import _apply_prompt_modifications, _enforce_single_profile


def process_batch_hybrid(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process video batch with HYBRID progress (alive-progress + Rich).

    Per manifesto recommendation:
    - alive-progress: Main video generation progress (maximum visual flair)
    - Rich: Detailed sub-operation logging (console output, panels)

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results
    """
    async_client, jobs, profile, run_dir = _setup_processing_hybrid(context)
    results = _execute_video_batch_hybrid(async_client, jobs, profile, run_dir)

    return {
        "total": results["total"],
        "success": results["success"],
        "cost": results["total_cost"],
        "output_dir": run_dir,
        "adjustments": results["adjustments"],
    }


def _setup_processing_hybrid(
    context: ProcessingContext,
) -> Tuple[AsyncReplicateClientEnhanced, List[MarkdownJob], Dict[str, Any], Path]:
    """Setup processing environment and discover inputs."""
    config = APIClientConfig(api_token=context.client.api_token, poll_interval=3)
    async_client = AsyncReplicateClientEnhanced(config=config)

    log_stage_emoji("preparing", "Discovering markdown jobs...")
    markdown_files = discover_markdown_jobs(context.input_dir)
    jobs = [parse_markdown_job(md_file) for md_file in markdown_files]
    logger.success(f"Found {len(jobs)} markdown jobs")

    log_stage_emoji("preparing", "Loading video profile...")
    active_profiles = load_active_profiles(context.profiles_dir)
    profile = _enforce_single_profile(active_profiles)
    logger.success(f"Loaded profile: {profile['name']}")

    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    dir_name = f"{timestamp}_IMG-TO-VID"
    run_dir = context.output_dir / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output: {run_dir}")

    return async_client, jobs, profile, run_dir


def _execute_video_batch_hybrid(
    async_client: AsyncReplicateClientEnhanced,
    jobs: List[MarkdownJob],
    profile: Dict[str, Any],
    run_dir: Path,
) -> Dict[str, Any]:
    """
    Execute batch with HYBRID progress (alive-progress main + Rich details).

    This follows the manifesto recommendation:
    - alive-progress handles the main visual progress bar with dual-line status
    - Rich handles detailed console logging with colors and formatting
    """
    total = len(jobs)

    hybrid = HybridVideoProgress()

    success_count = 0
    total_cost = 0.0
    all_adjustments = []

    with hybrid.track_generation(total, title="Video Generation Batch") as (
        bar,
        console,
    ):
        for job in jobs:
            video_name = job.markdown_file.stem

            try:
                hybrid.update_video_status(
                    video_name, "Initializing", "Setting up video context"
                )

                video_context = VideoProcessingContext(
                    client=async_client,
                    prompt_file=job.markdown_file,
                    image_url_file=job.markdown_file,
                    num_frames_file=job.markdown_file,
                    profile=profile,
                    run_dir=run_dir,
                    progress=None,
                    task_id=0,
                )

                video_cost, adjustment_info = _process_video_hybrid(
                    video_context, job, hybrid, video_name
                )

                success_count += 1
                total_cost += video_cost

                if adjustment_info and adjustment_info.get("reason"):
                    all_adjustments.append(
                        {
                            "prompt_file": job.markdown_file.name,
                            "profile": profile["name"],
                            **adjustment_info,
                        }
                    )

                hybrid.mark_success(video_name, video_cost)

            except Exception as e:
                hybrid.mark_error(video_name, str(e))
                logger.exception(e)
                raise

        hybrid.print_summary(total, success_count, total_cost)

    return {
        "success": success_count,
        "total": total,
        "total_cost": total_cost,
        "adjustments": all_adjustments,
    }


def _process_video_hybrid(
    context: VideoProcessingContext,
    job: MarkdownJob,
    hybrid: HybridVideoProgress,
    video_name: str,
) -> Tuple[float, Dict[str, Any]]:
    """Process single video with hybrid progress feedback."""

    hybrid.log_phase_start("Preparing", f"Loading inputs for {job.markdown_file.stem}")
    prompt = job.prompt
    image_url = job.image_url
    num_frames = job.num_frames

    prompt = _apply_prompt_modifications(prompt, context.profile)

    from .processor import _prepare_generation_params

    hybrid.update_video_status(video_name, "Preparing", "Building API parameters")
    params, adjustment_info = _prepare_generation_params(context.profile, num_frames)

    logger.info("=" * 60)
    hybrid.log_phase_start("Generating", f"Model: {context.profile['model_id']}")
    logger.info(f"Prompt: {prompt[:80]}...")
    logger.info(f"Image: {image_url[:80]}...")
    logger.info(
        f"Duration: {params.get('duration', params.get('num_frames', 'N/A'))}"
    )
    logger.info("=" * 60)

    hybrid.update_video_status(video_name, "Generating", "Sending API request")

    progress_callback = create_hybrid_api_callback(hybrid)

    video_url = context.client.generate_video_with_polling(
        model_name=context.profile["model_id"],
        image_url=image_url,
        prompt=prompt,
        params=params,
        progress_callback=progress_callback,
        image_url_param=context.profile.get("image_url_param", "image"),
    )

    if not video_url:
        raise Exception(f"No video URL returned from API for {video_name}")

    hybrid.update_video_status(video_name, "Downloading", "Fetching generated video")
    hybrid.log_phase_start("Downloading", f"URL: {video_url[:60]}...")

    video_filename = generate_video_filename(job.markdown_file.name)
    video_path = context.run_dir / video_filename
    download_video(video_url, video_path)

    video_cost = calculate_cost_from_params(context.profile, params, num_frames)

    hybrid.update_video_status(video_name, "Finalizing", "Saving documentation")
    hybrid.log_phase_start("Finalizing", "Generating reports and logs")

    gen_context = GenerationContext(
        prompt_file=job.markdown_file,
        image_url_file=job.markdown_file,
        num_frames_file=job.markdown_file,
        output_dir=context.run_dir,
        prompt=prompt,
        image_url=image_url,
        num_frames=num_frames,
        profile=context.profile,
        params=params,
        video_url=video_url,
        video_path=video_path,
        cost=video_cost,
        adjustment_info=adjustment_info,
    )
    video_filename_stem = video_path.stem
    save_generation_files(gen_context, video_filename_stem)

    return video_cost, adjustment_info
