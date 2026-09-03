"""Shared type definitions for the application."""

from pathlib import Path
from typing import TypedDict


class Bullet(TypedDict):
    """A parsed .md bullet file with its extracted data."""

    path: Path
    prompt: str
    reference_urls: list[str]
    frames: int | None
    duration: int | str | None
    references: dict[str, list[str]]
