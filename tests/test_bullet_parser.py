"""Tests for bullet_parser module."""

from unittest.mock import patch

import pytest

from src.processing.bullet_parser import (
    parse_bullet,
    read_bullets,
    validate_image_urls,
)


class TestParseBullet:
    def test_single_line_prompt(self):
        content = "A man walks on the beach.\n![start](https://example.com/frame.jpg)"
        prompt, urls, frames = parse_bullet(content)
        assert prompt == "A man walks on the beach."
        assert urls == ["https://example.com/frame.jpg"]
        assert frames is None

    def test_first_non_empty_line(self):
        content = "\n\nHello world\n![img](https://x.com/a.jpg)"
        prompt, _, _ = parse_bullet(content)
        assert prompt == "Hello world"

    def test_image_first_line_is_not_prompt(self):
        content = "![start](https://x.com/a.jpg)\nA real prompt"
        prompt, urls, _ = parse_bullet(content)
        assert prompt == "A real prompt"
        assert urls == ["https://x.com/a.jpg"]

    def test_empty_content_raises(self):
        with pytest.raises(ValueError, match="No prompt"):
            parse_bullet("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            parse_bullet("   \n   \n")

    def test_multiple_urls(self):
        content = "Prompt\n![a](https://example.com/1.jpg)\n![b](https://example.com/2.jpg)"
        _, urls, _ = parse_bullet(content)
        assert urls == ["https://example.com/1.jpg", "https://example.com/2.jpg"]

    def test_frames_extracted(self):
        content = "Prompt\n![a](https://example.com/1.jpg)\nframes: 96"
        _, _, frames = parse_bullet(content)
        assert frames == 96

    def test_frames_case_insensitive(self):
        content = "Prompt\nFRAMES: 60"
        _, _, frames = parse_bullet(content)
        assert frames == 60

    def test_format_warning_for_missing_bang(self):
        warnings: list[str] = []
        content = "Prompt\n[alt](https://example.com/1.jpg)"
        _, urls, _ = parse_bullet(content, warn=warnings.append)
        assert urls == []
        assert any("missing '!'" in w for w in warnings)


class TestValidateImageUrls:
    def test_split_valid_invalid(self):
        class FakeResp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with patch("src.processing.bullet_parser.urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [FakeResp(), ValueError("down")]
            valid, invalid = validate_image_urls(["https://a.com/1.jpg", "https://b.com/2.jpg"])
            assert valid == ["https://a.com/1.jpg"]
            assert invalid == ["https://b.com/2.jpg"]


class TestReadBullets:
    def test_empty_dir_returns_empty_list(self, tmp_path):
        bullets = read_bullets(tmp_path)
        assert bullets == []

    def test_dry_run_skips_head_validation(self, tmp_path):
        bullet = tmp_path / "b.md"
        bullet.write_text("Prompt\n![a](https://example.com/frame.jpg)\n")
        with patch("src.processing.bullet_parser.validate_image_urls") as mock_validate:
            bullets = read_bullets(tmp_path, dry_run=True)
            mock_validate.assert_not_called()
        assert len(bullets) == 1
        assert bullets[0]["reference_urls"] == ["https://example.com/frame.jpg"]

    def test_nested_bullets_found(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.md").write_text("Nested prompt\n")
        bullets = read_bullets(tmp_path, dry_run=True)
        assert len(bullets) == 1
        assert bullets[0]["path"].name == "b.md"

    def test_parse_failure_logs_and_continues(self, tmp_path):
        (tmp_path / "bad.md").write_text("![only](https://example.com/a.jpg)\n")
        (tmp_path / "good.md").write_text("Good prompt\n")
        bullets = read_bullets(tmp_path, dry_run=True)
        assert len(bullets) == 2
        assert bullets[0]["prompt"] == ""
        assert bullets[1]["prompt"] == "Good prompt"
