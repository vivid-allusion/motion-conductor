#!/usr/bin/env python
"""Standalone cost estimation script - calculates costs without generating videos."""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

from src.processing.input_discovery import discover_markdown_jobs, parse_markdown_job
from src.processing.profile_loader import load_active_profiles
from src.processing.cost_calculator import calculate_video_cost
from src.processing.duration_handler import process_duration
from src.processing.processor import _enforce_single_profile
from src.config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from src.models.triplet import MarkdownJob
from loguru import logger


def load_estimation_data() -> Tuple[Dict[str, Any], List[MarkdownJob]]:
    """
    Load single profile and discover markdown jobs.

    Returns:
        Tuple of (profile, jobs)

    Raises:
        Exception: If loading fails or wrong number of profiles
    """
    profiles = load_active_profiles(PROFILES_DIR)
    profile = _enforce_single_profile(profiles)
    logger.info(f"Using profile: {profile['name']}")

    markdown_files = discover_markdown_jobs(INPUT_DIR)
    jobs = [parse_markdown_job(md_file) for md_file in markdown_files]
    logger.info(f"Found {len(jobs)} markdown job files")

    return profile, jobs


def calculate_costs(
    profile: Dict[str, Any], jobs: List[MarkdownJob]
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Calculate costs for a single profile and all jobs.

    Args:
        profile: Profile configuration dictionary
        jobs: List of MarkdownJob objects

    Returns:
        Tuple of (duration_list, total_cost)
    """
    frame_data = []

    for job in jobs:
        try:
            frame_data.append(
                {"prompt": job.markdown_file.stem, "frames": job.num_frames}
            )
            logger.info(f"{job.markdown_file.stem}: {job.num_frames} frames")
        except Exception as e:
            logger.error(f"Failed to read frames from {job.markdown_file}: {e}")
            continue

    profile_total_seconds = 0
    duration_list = []

    for item in frame_data:
        adjusted_duration, was_adjusted, adjustment_info = process_duration(
            item["frames"], profile
        )

        if profile["duration_config"]["duration_type"] == "frames":
            fps = profile["duration_config"]["fps"]
            duration_seconds = int(adjusted_duration / fps)
        else:
            duration_seconds = adjusted_duration

        profile_total_seconds += duration_seconds
        duration_list.append(
            {
                "prompt": item["prompt"],
                "frames": item["frames"],
                "duration": duration_seconds,
                "adjusted": was_adjusted,
            }
        )

    total_cost = calculate_video_cost(profile, profile_total_seconds)
    cost_per_video = total_cost / len(jobs) if jobs else 0

    logger.info(
        f"Profile '{profile['name']}': ${total_cost:.4f} for {profile_total_seconds}s "
        f"total video ({cost_per_video:.4f} per video)"
    )

    return duration_list, total_cost


def generate_cost_report(
    profile: Dict[str, Any],
    duration_list: List[Dict[str, Any]],
    total_cost: float,
    num_jobs: int,
) -> Path:
    """
    Generate markdown cost estimation report for single profile.

    Args:
        profile: Profile configuration
        duration_list: List of video durations
        total_cost: Total estimated cost
        num_jobs: Number of markdown job files

    Returns:
        Path to generated report
    """
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    dir_name = f"{timestamp}_IMG-TO-VID"
    output_dir = OUTPUT_DIR / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "cost_estimate.md"

    cost_per_video = total_cost / num_jobs if num_jobs else 0

    with open(report_path, "w") as f:
        f.write("# Cost Estimation Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Profile:** {profile['name']}\n")
        f.write(f"- **Model:** {profile['model_id']}\n")
        f.write(f"- **Total Videos:** {num_jobs}\n")
        f.write(f"- **Total Estimated Cost:** ${total_cost:.4f}\n")
        f.write(f"- **Avg Cost/Video:** ${cost_per_video:.4f}\n\n")

        total_duration = sum(item["duration"] for item in duration_list)
        f.write(f"- **Total Video Duration:** {total_duration}s\n\n")

        f.write("## Video Duration Distribution\n\n")
        f.write("| Video | Input Frames | Video Duration |\n")
        f.write("|-------|--------------|----------------|\n")
        for item in duration_list:
            adjusted_marker = " *" if item.get("adjusted") else ""
            f.write(
                f"| {item['prompt']} | {item['frames']} | {item['duration']}s{adjusted_marker} |\n"
            )

        total_first = sum(item["duration"] for item in duration_list)
        f.write(f"| **TOTAL** | - | **{total_first}s** |\n\n")
        f.write("*\\* = Duration adjusted to meet model min/max constraints*\n\n")

        f.write("## Notes\n\n")
        f.write("- All pricing is time-based (cost per second of video output)\n")
        f.write("- This is an estimate based on the configured profile\n")
        f.write("- Actual costs may vary if generation fails or retries are needed\n")

    return report_path


def estimate_costs() -> None:
    """Calculate and report cost estimates without generating videos."""
    logger.info("Starting cost estimation...")

    try:
        profile, jobs = load_estimation_data()

        duration_list, total_cost = calculate_costs(profile, jobs)

        report_path = generate_cost_report(
            profile, duration_list, total_cost, len(jobs)
        )

        logger.info(f"Cost estimation report saved to: {report_path}")
        logger.success(f"Cost estimation complete! Report saved to: {report_path}")

    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise


if __name__ == "__main__":
    estimate_costs()
