"""Main entry point with verbose output enabled by default."""

import sys
from loguru import logger

from .api.client import ReplicateClient
from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.verbose_processor import process_batch_verbose
from .models.processing import ProcessingContext
from .models.video_processing import APIClientConfig
from .output.reporter import create_success_report, create_cost_report

# Lazy import for adjustments_reporter - only loaded when needed
from .utils.enhanced_logging import setup_dual_logging
from .utils.verbose_output import log_stage_emoji
from .utils.cleanup import archive_and_cleanup_logs
from .validation.environment import validate_environment, validate_input_directories
from .exceptions import VideoGenerationError, AuthenticationError, InputValidationError


def main() -> int:
    """Main entry point with verbose terminal output."""

    setup_dual_logging(enable_verbose=True)

    try:
        log_stage_emoji("starting", "Validating environment and authentication...")
        api_key = validate_environment()
        logger.success("Authentication successful")

        log_stage_emoji("preparing", "Validating input directories...")
        validate_input_directories(INPUT_DIR, PROFILES_DIR)
        logger.success("Input directory and profiles validated")

        config = APIClientConfig(api_token=api_key)
        client = ReplicateClient(config=config)

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
        create_success_report(results, output_dir)
        create_cost_report(results, output_dir)

        if results.get("adjustments"):
            from .reporting.adjustments_reporter import create_adjustments_report

            create_adjustments_report(
                adjustments=results["adjustments"],
                output_dir=output_dir,
                total_processed=results["total"],
            )
            logger.info(f"{len(results['adjustments'])} duration adjustments made")

        log_stage_emoji("saving", "Archiving log files...")
        try:
            archive_and_cleanup_logs(output_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup logs (non-fatal): {e}")

        logger.success("=" * 60)
        log_stage_emoji("complete", f"All processing complete!")
        logger.success(f"Success: {results['success']}/{results['total']} videos")
        logger.info(f"Total cost: ${results['cost']:.2f}")
        logger.info(f"Output: {output_dir}")
        logger.success("=" * 60)

        return 0

    except KeyboardInterrupt:
        log_stage_emoji("failed", "Interrupted by user")
        return 130
    except AuthenticationError as e:
        log_stage_emoji("failed", f"Authentication failed: {e}")
        return 2
    except InputValidationError as e:
        log_stage_emoji("failed", f"Input validation failed: {e}")
        return 3
    except VideoGenerationError as e:
        log_stage_emoji("failed", f"Video generation error: {e}")
        logger.exception("Full traceback:")
        return 4
    except Exception as e:
        log_stage_emoji("failed", f"Fatal error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
