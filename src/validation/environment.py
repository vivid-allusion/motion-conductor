"""Environment and directory validation utilities."""

from pathlib import Path
from loguru import logger

from ..auth import authenticate
from ..api.client import ReplicateClient
from ..models.video_processing import APIClientConfig
from ..exceptions import AuthenticationError, InputValidationError


def validate_environment() -> str:
    """
    Validate environment and authentication.

    Returns:
        API key if authentication successful

    Raises:
        AuthenticationError: If authentication fails
    """
    logger.info("Starting image-to-video generation")

    api_key = authenticate()
    if not api_key:
        logger.error("No API key found")
        raise AuthenticationError(
            "No API key found. Please set REPLICATE_API_TOKEN as an env var, "
            "store it via `pass insert openreel/replicate_api_token`, "
            "or add it to a .env file."
        )

    return api_key


def validate_input_directories(input_dir: Path, profiles_dir: Path) -> None:
    """
    Validate that profiles exist. Markdown file validation is deferred until
    after profiles are loaded, since profiles may specify custom input paths.

    Args:
        input_dir: Default directory for markdown job files (may be overridden by profiles)
        profiles_dir: Directory containing profile YAML files

    Raises:
        InputValidationError: If required directories don't exist or no profiles found
    """
    # Check default input directory exists (profiles may override this)
    if not input_dir.exists():
        error_msg = f"Default input directory does not exist: {input_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)

    # Check for profiles - this is required before we can check for markdown files
    # since profiles may specify custom input paths
    if not list(profiles_dir.glob("*.yaml")) and not list(profiles_dir.glob("*.yml")):
        error_msg = f"No profiles found in {profiles_dir}"
        logger.error(error_msg)
        raise InputValidationError(error_msg)

    logger.info("Profiles directory validated successfully")


def bootstrap_pipeline(input_dir: Path, profiles_dir: Path) -> ReplicateClient:
    """Validate environment and create configured API client.

    Args:
        input_dir: Default directory for markdown job files
        profiles_dir: Directory containing profile YAML files

    Returns:
        Configured ReplicateClient ready for use

    Raises:
        AuthenticationError: If authentication fails
        InputValidationError: If required directories don't exist
    """
    api_key = validate_environment()
    validate_input_directories(input_dir, profiles_dir)
    config = APIClientConfig(api_token=api_key)
    return ReplicateClient(config=config)
