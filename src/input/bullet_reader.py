"""Read and parse markdown bullet files for video generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from loguru import logger

_FRAMES_RE = re.compile(r"^frames:\s*(\d+)", re.IGNORECASE)


def _parse_bullet_md(content: str) -> dict[str, Any]:
    """Parse a single bullet .md file, extracting prompt, URLs, and frame count."""
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

    prompt = ""
    if lines:
        l0 = lines[0]
        if not l0.startswith("!["):
            prompt = l0

    urls: list[str] = []
    frames = None
    for ln in lines:
        m = re.search(r"!\[.*?\]\((https?://[^)]+)\)", ln)
        if m:
            urls.append(m.group(1))
        if frames is None:
            fm = _FRAMES_RE.match(ln)
            if fm:
                frames = int(fm.group(1))

    return {
        "prompt": prompt,
        "reference_urls": urls,
        "frames": frames,
    }


def read_bullets(input_dir: Path) -> list[dict[str, Any]]:
    """Read bullet .md files from input_dir, extract prompt, ref URLs, frames."""
    md_files = sorted(input_dir.rglob("*.md"))
    bullets: list[dict[str, Any]] = []
    for md_path in md_files:
        parsed = _parse_bullet_md(md_path.read_text(encoding="utf-8"))
        parsed["path"] = md_path
        bullets.append(parsed)

    if not bullets:
        logger.error(f"No .md files found in {input_dir}")
        raise FileNotFoundError(f"No .md files found in {input_dir}")

    logger.info(f"Discovered {len(bullets)} bullet(s) in {input_dir}")
    return bullets
