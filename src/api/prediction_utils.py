"""Shared prediction output parsing utilities."""

from typing import Any, Optional


def extract_video_url(output: Any) -> Optional[str]:
    """Extract video URL from prediction output, handling multiple formats.

    Handles these output formats (checked in order):
    1. Plain string URL
    2. Object with .url attribute (e.g., FileOutput)
    3. List of strings or objects
    4. Fallback: string conversion if starts with 'http'

    Args:
        output: Prediction output value (could be str, FileOutput, list, etc.)

    Returns:
        Video URL string if found, None otherwise
    """
    if not output:
        return None

    if isinstance(output, str):
        return output

    if hasattr(output, "url"):
        return output.url

    if isinstance(output, list) and len(output) > 0:
        first_item = output[0]
        if hasattr(first_item, "url"):
            return first_item.url
        elif isinstance(first_item, str):
            return first_item

    result_str = str(output)
    if result_str.startswith("http"):
        return result_str

    return None
