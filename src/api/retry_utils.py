"""Shared retry utilities for API clients."""

from typing import Tuple


def compute_retry_delay(
    error: Exception, attempt: int, rate_limit_delay: int
) -> Tuple[int, bool]:
    """Compute wait time and rate-limit status from an error.

    Args:
        error: The exception that triggered the retry
        attempt: Current attempt number (1-based)
        rate_limit_delay: Seconds to wait when rate limited

    Returns:
        Tuple of (wait_time_seconds, is_rate_limited)
    """
    err_str = str(error)
    is_rate_limited = "429" in err_str or "rate" in err_str.lower()

    if is_rate_limited:
        wait_time = rate_limit_delay
    else:
        wait_time = 2**attempt

    return wait_time, is_rate_limited
