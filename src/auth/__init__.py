"""Authentication module — 4-tier env var hierarchy.

Priority:
    1. Already-set env var (injected by OpenReel TUI or cloud wrapper)
    2. pass show studiolot/<key> (GPG-encrypted, optional)
    3. .env file in project root (standalone mode)
    4. Raise AuthenticationError if no key found
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
from loguru import logger
from dotenv import load_dotenv

REQUIRED_KEY = "REPLICATE_API_TOKEN"


class AuthenticationError(Exception):
    """Raised when no API token can be found from any source."""


def _try_pass(key_name: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["pass", "show", f"studiolot/{key_name}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info("Retrieved {} from pass", key_name)
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def authenticate(config_name: Optional[str] = None) -> str:
    api_token = os.getenv(REQUIRED_KEY)
    if api_token:
        logger.info("Using {} from environment", REQUIRED_KEY)
        return api_token

    api_token = _try_pass(REQUIRED_KEY.lower())
    if api_token:
        os.environ[REQUIRED_KEY] = api_token
        return api_token

    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        api_token = os.getenv(REQUIRED_KEY)
        if api_token:
            logger.info("Loaded {} from {}", REQUIRED_KEY, env_path)
            return api_token

    raise AuthenticationError(
        "ERROR: REPLICATE_API_TOKEN not set.\n"
        "  - Set as env var  (export REPLICATE_API_TOKEN=...)\n"
        "  - Store in pass   (pass insert studiolot/replicate_api_token)\n"
        "  - Add to .env     (echo REPLICATE_API_TOKEN=... > .env)"
    )


__all__ = ["authenticate", "AuthenticationError"]
