"""
Custom exceptions for video generation tool.

This module defines a hierarchy of exceptions for different error scenarios:
- VideoGenerationError: Base exception for all video generation errors
- AuthenticationError: API authentication failures
- InputValidationError: Invalid input data or missing files
- ProfileValidationError: Invalid profile configuration
- APIError: General API communication errors

All exceptions inherit from VideoGenerationError for consistent error handling.
"""


class VideoGenerationError(Exception):
    """Base exception for video generation errors."""
    pass


class AuthenticationError(VideoGenerationError):
    """Raised when authentication fails."""
    pass


class InputValidationError(VideoGenerationError):
    """Raised when input validation fails."""
    pass


class ProfileValidationError(VideoGenerationError):
    """Raised when profile validation fails."""
    pass


class APIError(VideoGenerationError):
    """Raised when API calls fail."""
    pass


def handle_main_exception(e: Exception, log_error, log_exception) -> int:
    """
    Handle exceptions from main() with appropriate logging and exit codes.

    Returns exit code: 130=interrupt, 2=auth, 3=input, 4=generation, 1=general.
    """
    if isinstance(e, KeyboardInterrupt):
        log_error("Interrupted by user")
        return 130
    elif isinstance(e, AuthenticationError):
        log_error(f"Authentication failed: {e}")
        return 2
    elif isinstance(e, InputValidationError):
        log_error(f"Input validation failed: {e}")
        return 3
    elif isinstance(e, VideoGenerationError):
        log_error(f"Video generation error: {e}")
        log_exception("Full traceback:")
        return 4
    else:
        log_error(f"Fatal error: {e}")
        log_exception("Full traceback:")
        return 1


