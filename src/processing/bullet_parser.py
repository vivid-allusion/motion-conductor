"""Bullet markdown parsing for video generation.

Parses bullet .md files and extracts:
- Text prompt from the first non-empty, non-image line
- Reference URLs from markdown ![alt](URL) syntax — empty alt feeds the
  primary slot, a named alt feeds the named slot (when declared)
- Optional frame count from a `frames: N` line (deprecated, converted via fps)
- Optional raw duration from a `duration: <int|token>` line (verbatim)

Format:
    Line 1: Text prompt
    Lines 2+: ![alt](URL), frames: N and/or duration: <value>
"""

import re
import sys
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from ..datatypes import Bullet

if TYPE_CHECKING:
    from collections.abc import Callable

_FRAMES_RE = re.compile(r"^frames:\s*(\d+)", re.IGNORECASE)
_DURATION_RE = re.compile(r"^duration:\s*(\S+)", re.IGNORECASE)

_IMG_URL_PATTERN = re.compile(r"!\[([^\]]*)\]\((https?://[^\)]+)\)")
_LINK_WITHOUT_BANG = re.compile(r"(?<!!)\[.*?\]\((https?://[^\)]+)\)")
_BANG_SPACE_PATTERN = re.compile(r"! +\[.*?\]\(.*?\)")
_PAREN_SPACE_PATTERN = re.compile(r"!\[.*?\] +\(.*?\)")
_SWAPPED_PATTERN = re.compile(r"!\[(https?://[^\]]+)\]\([^\)]+\)")
_UNCLOSED_PATTERN = re.compile(r"!\[.*?\]\([^\)]*$")
_HTML_IMG_PATTERN = re.compile(r"<img[^>]*src\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
_NON_HTTP_URL = re.compile(
    r"!\[.*?\]\((?!https?://)(\.\.?/|\.\.?\\|//|/|data:|file:|ftp:|[A-Za-z]:\\|\w+://)[^\)]+\)"
)


def _check_line(line: str, lineno: int, warn: "Callable[[str], None] | None") -> None:
    """Inspect a line for common image-embed formatting mistakes."""
    if warn is None:
        return

    if _BANG_SPACE_PATTERN.search(line):
        warn(f"Line {lineno}: space between '!' and '[' — use ![alt](URL) not ! [alt](URL)")

    if _PAREN_SPACE_PATTERN.search(line):
        warn(f"Line {lineno}: space before '(' — use ![alt](URL) not ![alt] (URL)")

    if _SWAPPED_PATTERN.search(line):
        warn(f"Line {lineno}: URL and alt text appear swapped. Use ![alt](URL), not ![URL](alt)")

    if _UNCLOSED_PATTERN.search(line):
        warn(f"Line {lineno}: unclosed parenthesis — missing ')' after URL")

    if _LINK_WITHOUT_BANG.search(line):
        warn(f"Line {lineno}: missing '!' prefix — use ![alt](URL) not [alt](URL)")

    if _HTML_IMG_PATTERN.search(line):
        warn(f"Line {lineno}: HTML <img> tag found. Use markdown ![alt](URL) instead")

    if _NON_HTTP_URL.search(line):
        warn(
            f"Line {lineno}: image URL does not start with https:// — "
            "only remote URLs are supported"
        )


def _coerce_duration(raw: str) -> int | str:
    """Return int for numeric tokens, the raw string otherwise (verbatim)."""
    try:
        return int(raw)
    except ValueError:
        return raw


def _route_image(
    alt: str,
    url: str,
    urls: list[str],
    references: dict[str, list[str]],
    declared_slots: list[str] | None,
) -> None:
    """Route a URL: empty alt or no slot schema → primary; else named slot.

    Raises:
        ValueError: alt text not declared in the profile's slot schema.
    """
    alt = alt.strip()
    if not alt or declared_slots is None:
        urls.append(url)
        return
    if alt not in declared_slots:
        raise ValueError(
            f"Unknown reference slot '{alt}' — declared slots: {declared_slots}"
        )
    references.setdefault(alt, []).append(url)


def parse_bullet(
    markdown_content: str,
    warn: "Callable[[str], None] | None" = None,
    declared_slots: list[str] | None = None,
) -> tuple[str, list[str], int | None, int | str | None, dict[str, list[str]]]:
    """Parse a .md bullet, returning (prompt, urls, frames, duration, references).

    Raises:
        ValueError: If no prompt found or an alt is not a declared slot.
    """
    lines = markdown_content.split("\n")
    prompt = ""
    urls: list[str] = []
    frames: int | None = None
    duration: int | str | None = None
    references: dict[str, list[str]] = {}

    seen_prompt = False
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if not seen_prompt:
            first_match = _IMG_URL_PATTERN.search(line)
            if first_match:
                _route_image(
                    first_match.group(1), first_match.group(2), urls, references, declared_slots
                )
                continue
            prompt = stripped
            seen_prompt = True
            continue

        match = _IMG_URL_PATTERN.search(line)
        if match:
            _route_image(match.group(1), match.group(2), urls, references, declared_slots)
        elif _FRAMES_RE.match(stripped):
            if frames is None:
                frames = int(_FRAMES_RE.match(stripped).group(1))
        elif (duration_match := _DURATION_RE.match(stripped)):
            if duration is None:
                duration = _coerce_duration(duration_match.group(1))
        else:
            _check_line(line, lineno, warn)

    if not prompt:
        raise ValueError("No prompt text found in markdown")

    return prompt, urls, frames, duration, references


def validate_image_urls(urls: list[str], timeout: float = 5.0) -> tuple[list[str], list[str]]:
    """Validate image URLs are reachable via HEAD request.

    Returns:
        Tuple of (valid_urls, invalid_urls). Invalid URLs are stripped.
    """
    valid: list[str] = []
    invalid: list[str] = []
    headers = {"User-Agent": "MotionConductor/1.0"}
    for url in urls:
        try:
            req = urllib.request.Request(url, method="HEAD", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status >= 400:
                    invalid.append(url)
                else:
                    valid.append(url)
        except Exception:
            invalid.append(url)
    return valid, invalid


def read_bullets(
    input_dir: Path,
    dry_run: bool = False,
    declared_slots: list[str] | None = None,
) -> list[Bullet]:
    """Read .md bullets from input_dir, extract prompt + URLs + frames + duration.

    declared_slots (from the profile's `slots:` key) enables named-slot
    routing; without it every alt falls back to the primary slot.
    Returns [] (with a warning) when the directory holds no .md files.
    """
    md_files = sorted(input_dir.rglob("*.md"))
    result: list[Bullet] = []
    for md_path in md_files:
        content = md_path.read_text(encoding="utf-8")
        prompt = ""
        urls: list[str] = []
        frames: int | None = None
        duration: int | str | None = None
        references: dict[str, list[str]] = {}
        try:
            prompt, urls, frames, duration, references = parse_bullet(
                content, warn=logger.warning, declared_slots=declared_slots
            )
        except ValueError as e:
            logger.warning(f"Failed to parse {md_path.name}: {e}")
        if urls and not dry_run:
            valid, invalid = validate_image_urls(urls)
            for url in invalid:
                logger.warning(f"Unreachable image URL in {md_path.name}: {url}")
            urls = valid
            if not urls:
                logger.warning(
                    f"No reachable image URLs in {md_path.name} "
                    f"— treating as text-to-video"
                )
        result.append(
            {
                "path": md_path,
                "prompt": prompt,
                "reference_urls": urls,
                "frames": frames,
                "duration": duration,
                "references": references,
            }
        )
    if not result:
        logger.warning(f"No .md files found in {input_dir}")
        return result
    sys.stderr.write(f"Discovered {len(result)} bullet file(s) in {input_dir}\n")
    return result
