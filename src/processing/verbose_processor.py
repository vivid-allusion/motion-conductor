"""Enhanced processor with verbose terminal output."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

from loguru import logger

from ..api.async_client_enhanced import AsyncReplicateClientEnhanced
from ..utils.verbose_output import VerboseContext, log_stage_emoji
from ..utils.epic_progress import VideoGenerationProgress, create_api_callback
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
from .processor import _apply_prompt_modifications, _enforce_single_profile, _record_adjustment


def process_batch_verbose(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process video batch with verbose terminal output.

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results
    """
    with VerboseContext() as verbose:
        async_client, jobs, profile, run_dir = _setup_processing(context)
        results = _execute_video_batch(async_client, jobs, profile, run_dir)
        return _generate_summary(results, run_dir)


def _setup_processing(
    context: ProcessingContext,
) -> Tuple[AsyncReplicateClientEnhanced, List[MarkdownJob], Dict[str, Any], Path]:
    """Setup processing environment and discover inputs."""
    config = APIClientConfig(api_token=context.client.api_token, poll_interval=3)
    async_client = AsyncReplicateClientEnhanced(config=config)

    log_stage_emoji("preparing", "Loading video profile...")
    active_profiles = load_active_profiles(context.profiles_dir)
    profile = _enforce_single_profile(active_profiles)
    logger.success(f"Loaded profile: {profile['name']}")

    log_stage_emoji("preparing", "Discovering markdown jobs...")

    custom_input_path = profile.get("custom_input_path")
    markdown_files = discover_markdown_jobs(context.input_dir, custom_input_path)
    jobs = [parse_markdown_job(md_file) for md_file in markdown_files]
    logger.success(f"Found {len(jobs)} markdown jobs")

    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")

    custom_output_path = profile.get("custom_output_path")
    base_output_dir = (
        Path(custom_output_path) if custom_output_path else context.output_dir
    )

    dir_name = f"{timestamp}_IMG-TO-VID"
    run_dir = base_output_dir / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output: {run_dir}")

    return async_client, jobs, profile, run_dir


def _execute_video_batch(
    async_client: AsyncReplicateClientEnhanced,
    jobs: List[MarkdownJob],
    profile: Dict[str, Any],
    run_dir: Path,
) -> Dict[str, Any]:
    """Execute batch video processing with epic progress tracking."""
    total = len(jobs)

    epic_progress = VideoGenerationProgress()

    success_count = 0
    total_cost = 0.0
    all_adjustments = []

    with epic_progress.track_generation(total, title="Video Generation Batch") as (
        progress,
        main_task,
    ):
        for job in jobs:
            video_name = job.markdown_file.stem

            try:
                epic_progress.update_status(
                    progress,
                    main_task,
                    status="Starting...",
                    video_name=video_name,
                    phase="Initializing",
                )

                video_context = VideoProcessingContext(
                    client=async_client,
                    prompt_file=job.markdown_file,
                    image_url_file=job.markdown_file,
                    num_frames_file=job.markdown_file,
                    profile=profile,
                    run_dir=run_dir,
                    progress=progress,
                    task_id=main_task,
                )

                video_cost, adjustment_info = _process_video_verbose(
                    video_context, job, epic_progress
                )

                success_count += 1
                total_cost += video_cost

                _record_adjustment(adjustment_info, job.markdown_file.name, profile["name"], all_adjustments)

                epic_progress.mark_success(
                    progress, main_task, video_name, video_cost
                )

                progress.advance(main_task)

                epic_progress.update_with_cost(
                    progress,
                    main_task,
                    status="Complete",
                    total_cost=total_cost,
                    video_name=video_name,
                )

            except Exception as e:
                epic_progress.mark_error(progress, main_task, video_name, str(e))
                logger.exception(e)
                raise

    return {
        "success_count": success_count,
        "total": total,
        "total_cost": total_cost,
        "adjustments": all_adjustments,
    }


def _generate_summary(results: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
    """Generate final processing summary."""
    total = results["total"]
    success_count = results["success_count"]
    total_cost = results["total_cost"]

    logger.success(f"Completed {success_count}/{total} videos")
    logger.info(f"Total cost: ${total_cost:.2f}")

    return {
        "total": total,
        "success": success_count,
        "cost": total_cost,
        "output_dir": run_dir,
        "adjustments": results["adjustments"],
    }


def _process_video_verbose(
    context: VideoProcessingContext,
    job: MarkdownJob,
    epic_progress: VideoGenerationProgress,
) -> Tuple[float, Dict[str, Any]]:
    """Process single video with verbose output and polling."""

    log_stage_emoji("preparing", f"Loading inputs for {job.markdown_file.stem}")
    prompt = job.prompt
    image_url = job.image_url
    num_frames = job.num_frames

    prompt = _apply_prompt_modifications(prompt, context.profile)

    video_name = job.markdown_file.stem

    params, adjustment_info = _prepare_params_verbose(context.profile, num_frames)

    epic_progress.update_status(
        context.progress,
        context.task_id,
        status="Preparing API call",
        video_name=video_name,
        phase="Preparing",
    )

    logger.info("=" * 60)
    log_stage_emoji("starting", f"Generating: {video_name}")
    logger.info(f"Prompt: {prompt[:80]}...")
    logger.info(f"Image: {image_url[:80]}...")
    logger.info(f"Model: {context.profile['model_id']}")
    logger.info(
        f"Duration: {params.get('duration', params.get('num_frames', 'N/A'))}"
    )
    logger.info("=" * 60)

    progress_callback = create_api_callback(context.progress, context.task_id)

    video_url = context.client.generate_video_with_polling(
        model_name=context.profile["model_id"],
        image_url=image_url,
        prompt=prompt,
        params=params,
        progress_callback=progress_callback,
        image_url_param=context.profile.get("image_url_param", "image"),
    )

    if not video_url:
        error_msg = f"No video URL returned from API for {video_name}"
        logger.error(error_msg)
        raise Exception(error_msg)

    epic_progress.update_status(
        context.progress,
        context.task_id,
        status="Downloading video",
        video_name=video_name,
        phase="Downloading",
    )

    video_filename = generate_video_filename(job.markdown_file.name)
    video_path = context.run_dir / video_filename
    download_video(video_url, video_path)

    video_cost = calculate_cost_from_params(context.profile, params, num_frames)

    epic_progress.update_status(
        context.progress,
        context.task_id,
        status="Saving documentation",
        video_name=video_name,
        phase="Finalizing",
    )

    gen_context = GenerationContext.from_video_result(
        job=job,
        output_dir=context.run_dir,
        profile=context.profile,
        params=params,
        prompt=prompt,
        video_url=video_url,
        video_path=video_path,
        cost=video_cost,
        adjustment_info=adjustment_info,
    )
    video_filename_stem = video_path.stem
    save_generation_files(gen_context, video_filename_stem)

    log_stage_emoji("complete", f"Completed: {video_path.name} (${video_cost:.2f})")

    return video_cost, adjustment_info


def _prepare_params_verbose(
    profile: Dict[str, Any], num_frames: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Prepare parameters with verbose logging of adjustments."""
    from .processor import _prepare_generation_params

    params, adjustment_info = _prepare_generation_params(profile, num_frames)

    if adjustment_info and adjustment_info.get("reason"):
        logger.warning(f"Duration adjusted: {adjustment_info['reason']}")
        if adjustment_info.get("type") == "seconds":
            logger.info(
                f"  Original: {adjustment_info['original_seconds']}s ({adjustment_info['original_frames']} frames)"
            )
            logger.info(f"  Adjusted: {adjustment_info['adjusted_seconds']}s")
        else:
            logger.info(f"  Original: {adjustment_info['original']} frames")
            logger.info(f"  Adjusted: {adjustment_info['adjusted']} frames")

    return params, adjustment_info
