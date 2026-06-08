"""Main entry point with verbose output enabled by default."""

import sys
from loguru import logger

from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.verbose_processor import process_batch_verbose
from .models.processing import ProcessingContext
from .output.reporter import generate_all_reports

# Lazy import for adjustments_reporter - only loaded when needed
from .utils.enhanced_logging import setup_dual_logging
from .utils.verbose_output import log_stage_emoji
from .utils.cleanup import archive_and_cleanup_logs
from .validation.environment import bootstrap_pipeline
from .exceptions import handle_main_exception


def main() -> int:
    """Main entry point with verbose terminal output."""

    setup_dual_logging(enable_verbose=True)

    try:
        log_stage_emoji("starting", "Validating environment and authentication...")
        client = bootstrap_pipeline(INPUT_DIR, PROFILES_DIR)

        context = ProcessingContext(
            client=client,
            input_dir=INPUT_DIR,
            profiles_dir=PROFILES_DIR,
            output_dir=OUTPUT_DIR,
            progress=None,
        )

        log_stage_emoji("processing", "Starting video generation batch...")
        results = process_batch_verbose(context)

        log_stage_emoji("saving", "Generating reports...")
        output_dir = results["output_dir"]
        generate_all_reports(results, output_dir)

        log_stage_emoji("saving", "Archiving log files...")
        archive_and_cleanup_logs(output_dir)

        logger.success("=" * 60)
        log_stage_emoji("complete", f"All processing complete!")
        logger.success(f"Success: {results['success']}/{results['total']} videos")
        logger.info(f"Total cost: ${results['cost']:.2f}")
        logger.info(f"Output: {output_dir}")
        logger.success("=" * 60)

        return 0

    except Exception as e:
        return handle_main_exception(
            e,
            log_error=lambda msg: log_stage_emoji("failed", msg),
            log_exception=logger.exception,
        )


if __name__ == "__main__":
    sys.exit(main())
