"""Main entry point with HYBRID progress (alive-progress WAVES + Rich logging)."""

import sys
from loguru import logger

from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.hybrid_processor import process_batch_hybrid
from .models.processing import ProcessingContext
from .output.reporter import generate_all_reports
from .utils.enhanced_logging import setup_dual_logging
from .utils.verbose_output import log_stage_emoji
from .utils.cleanup import archive_and_cleanup_logs
from .validation.environment import bootstrap_pipeline
from .exceptions import handle_main_exception


def main() -> int:
    """
    Main entry point with HYBRID progress (manifesto recommended approach).

    Uses BOTH libraries as recommended:
    - alive-progress: Main task with WAVES animation (maximum visual flair!)
    - Rich: Detailed sub-operation logging (professional formatting)
    """

    setup_dual_logging(enable_verbose=True)

    try:
        log_stage_emoji(
            "starting", "Initializing HYBRID mode (alive-progress WAVES + Rich)"
        )
        client = bootstrap_pipeline(INPUT_DIR, PROFILES_DIR)
        logger.success("Authentication successful")

        context = ProcessingContext(
            client=client,
            input_dir=INPUT_DIR,
            profiles_dir=PROFILES_DIR,
            output_dir=OUTPUT_DIR,
            progress=None,
        )

        logger.info("=" * 70)
        logger.info("HYBRID MODE: alive-progress WAVES + Rich Console Logging")
        logger.info("=" * 70)

        results = process_batch_hybrid(context)

        log_stage_emoji("saving", "Generating reports...")
        output_dir = results["output_dir"]
        generate_all_reports(results, output_dir)

        log_stage_emoji("saving", "Archiving log files...")
        archive_and_cleanup_logs(output_dir)

        logger.info("=" * 70)
        logger.success(f"Total cost: ${results['cost']:.2f}")
        logger.info(f"Output: {output_dir}")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        return handle_main_exception(
            e,
            log_error=lambda msg: log_stage_emoji("failed", msg),
            log_exception=logger.exception,
        )


if __name__ == "__main__":
    sys.exit(main())
