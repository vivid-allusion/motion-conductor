"""Timestamped run directory creation."""
from pathlib import Path
from datetime import datetime


def create_timestamped_run_dir(base_dir: Path) -> Path:
    """Create a timestamped IMG-TO-VID run directory.

    Args:
        base_dir: The parent directory under which to create the run directory.

    Returns:
        Path to the created run directory.
    """
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    dir_name = f"{timestamp}_IMG-TO-VID"
    run_dir = base_dir / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
