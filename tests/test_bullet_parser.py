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
        prompt, urls, frames, duration, references = parse_bullet(content)
        assert prompt == "A man walks on the beach."
        assert urls == ["https://example.com/frame.jpg"]
        assert frames is None
        assert duration is None
        assert references == {}

    def test_first_non_empty_line(self):
        content = "\n\nHello world\n![img](https://x.com/a.jpg)"
        prompt, _, _, _, _ = parse_bullet(content)
        assert prompt == "Hello world"

    def test_image_first_line_is_not_prompt(self):
        content = "![start](https://x.com/a.jpg)\nA real prompt"
        prompt, urls, _, _, _ = parse_bullet(content)
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
        _, urls, _, _, _ = parse_bullet(content)
        assert urls == ["https://example.com/1.jpg", "https://example.com/2.jpg"]

    def test_frames_extracted(self):
        content = "Prompt\n![a](https://example.com/1.jpg)\nframes: 96"
        _, _, frames, _, _ = parse_bullet(content)
        assert frames == 96

    def test_frames_case_insensitive(self):
        content = "Prompt\nFRAMES: 60"
        _, _, frames, _, _ = parse_bullet(content)
        assert frames == 60

    def test_format_warning_for_missing_bang(self):
        warnings: list[str] = []
        content = "Prompt\n[alt](https://example.com/1.jpg)"
        _, urls, _, _, _ = parse_bullet(content, warn=warnings.append)
        assert urls == []
        assert any("missing '!'" in w for w in warnings)

    def test_duration_integer(self):
        content = "Prompt\nduration: 5"
        _, _, _, duration, _ = parse_bullet(content)
        assert duration == 5

    def test_duration_token_verbatim(self):
        content = "Prompt\nduration: auto"
        _, _, _, duration, _ = parse_bullet(content)
        assert duration == "auto"

    def test_duration_negative_one_is_int(self):
        content = "Prompt\nduration: -1"
        _, _, _, duration, _ = parse_bullet(content)
        assert duration == -1

    def test_duration_and_frames_both_parsed(self):
        content = "Prompt\nframes: 96\nduration: auto"
        _, _, frames, duration, _ = parse_bullet(content)
        assert frames == 96
        assert duration == "auto"

    def test_duration_case_insensitive(self):
        content = "Prompt\nDURATION: 8"
        _, _, _, duration, _ = parse_bullet(content)
        assert duration == 8

    def test_named_slot_routed_when_declared(self):
        content = "Prompt\n![reference_images](https://example.com/1.jpg)"
        _, urls, _, _, references = parse_bullet(
            content, declared_slots=["reference_images"]
        )
        assert urls == []
        assert references == {"reference_images": ["https://example.com/1.jpg"]}

    def test_empty_alt_stays_primary_with_schema(self):
        content = "Prompt\n![](https://example.com/1.jpg)"
        _, urls, _, _, references = parse_bullet(
            content, declared_slots=["reference_images"]
        )
        assert urls == ["https://example.com/1.jpg"]
        assert references == {}

    def test_unknown_alt_defaults_to_primary_with_warning(self):
        content = "Prompt\n![foo](https://example.com/1.jpg)"
        warnings: list[str] = []
        _, urls, _, _, references = parse_bullet(
            content,
            warn=warnings.append,
            declared_slots=["reference_images"],
        )
        assert urls == ["https://example.com/1.jpg"]
        assert references == {}
        assert any("Unknown reference slot 'foo'" in w for w in warnings)

    def test_primary_slot_name_alt_routes_to_primary(self):
        content = "Prompt\n![image](https://example.com/1.jpg)"
        _, urls, _, _, references = parse_bullet(
            content, declared_slots=["audio"], primary_slot="image"
        )
        assert urls == ["https://example.com/1.jpg"]
        assert references == {}

    def test_custom_primary_slot_name_alt_routes_to_primary(self):
        content = "Prompt\n![start_image](https://example.com/1.jpg)"
        _, urls, _, _, references = parse_bullet(
            content, declared_slots=["end_image"], primary_slot="start_image"
        )
        assert urls == ["https://example.com/1.jpg"]
        assert references == {}

    def test_primary_slot_name_not_stolen_from_declared(self):
        content = "Prompt\n![audio](https://example.com/1.jpg)"
        _, urls, _, _, references = parse_bullet(
            content, declared_slots=["audio"], primary_slot="image"
        )
        assert urls == []
        assert references == {"audio": ["https://example.com/1.jpg"]}

    def test_named_alt_falls_back_to_primary_without_schema(self):
        content = "Prompt\n![reference_images](https://example.com/1.jpg)"
        _, urls, _, _, references = parse_bullet(content)
        assert urls == ["https://example.com/1.jpg"]
        assert references == {}

    def test_multi_url_same_slot_appends(self):
        content = (
            "Prompt\n![reference_images](https://example.com/1.jpg)\n"
            "![reference_images](https://example.com/2.jpg)"
        )
        _, _, _, _, references = parse_bullet(content, declared_slots=["reference_images"])
        assert references == {
            "reference_images": [
                "https://example.com/1.jpg",
                "https://example.com/2.jpg",
            ]
        }


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

    def test_parse_failure_rejects_bullet(self, tmp_path):
        (tmp_path / "bad.md").write_text("![only](https://example.com/a.jpg)\n")
        (tmp_path / "good.md").write_text("Good prompt\n")
        bullets = read_bullets(tmp_path, dry_run=True)
        assert len(bullets) == 1
        assert bullets[0]["prompt"] == "Good prompt"

    def test_all_rejected_returns_empty(self, tmp_path):
        (tmp_path / "bad.md").write_text("![only](https://example.com/a.jpg)\n")
        assert read_bullets(tmp_path, dry_run=True) == []

    def test_unreachable_primary_url_rejects_bullet(self, tmp_path):
        bullet = tmp_path / "b.md"
        bullet.write_text("Prompt\n![](https://example.com/frame.jpg)\n")
        with patch(
            "src.processing.bullet_parser.validate_image_urls",
            return_value=([], ["https://example.com/frame.jpg"]),
        ):
            bullets = read_bullets(tmp_path, dry_run=False)
        assert bullets == []

    def test_unreachable_named_slot_url_rejects_bullet(self, tmp_path):
        bullet = tmp_path / "b.md"
        bullet.write_text(
            "Prompt\n"
            "![](https://example.com/frame.jpg)\n"
            "![audio](https://example.com/dead.wav)\n"
        )
        with patch(
            "src.processing.bullet_parser.validate_image_urls",
            return_value=(["https://example.com/frame.jpg"], ["https://example.com/dead.wav"]),
        ):
            bullets = read_bullets(tmp_path, dry_run=False, declared_slots=["audio"])
        assert bullets == []

    def test_reachable_media_keeps_bullet(self, tmp_path):
        bullet = tmp_path / "b.md"
        bullet.write_text(
            "Prompt\n"
            "![](https://example.com/frame.jpg)\n"
            "![audio](https://example.com/music.wav)\n"
        )
        with patch(
            "src.processing.bullet_parser.validate_image_urls",
            return_value=(
                ["https://example.com/frame.jpg", "https://example.com/music.wav"],
                [],
            ),
        ):
            bullets = read_bullets(tmp_path, dry_run=False, declared_slots=["audio"])
        assert len(bullets) == 1
        assert bullets[0]["reference_urls"] == ["https://example.com/frame.jpg"]
        assert bullets[0]["references"] == {"audio": ["https://example.com/music.wav"]}

    def test_declared_slots_passed_to_parser(self, tmp_path):
        bullet = tmp_path / "b.md"
        bullet.write_text("Prompt\n![reference_images](https://example.com/frame.jpg)\n")
        bullets = read_bullets(tmp_path, dry_run=True, declared_slots=["reference_images"])
        assert bullets[0]["reference_urls"] == []
        assert bullets[0]["references"] == {
            "reference_images": ["https://example.com/frame.jpg"]
        }

    def test_primary_slot_passed_to_parser(self, tmp_path):
        bullet = tmp_path / "b.md"
        bullet.write_text("Prompt\n![start_image](https://example.com/frame.jpg)\n")
        bullets = read_bullets(
            tmp_path, dry_run=True, declared_slots=["end_image"], primary_slot="start_image"
        )
        assert bullets[0]["reference_urls"] == ["https://example.com/frame.jpg"]
        assert bullets[0]["references"] == {}

    def test_duration_and_references_in_bullet(self, tmp_path):
        bullet = tmp_path / "b.md"
        bullet.write_text("Prompt\nduration: auto\n![](https://example.com/frame.jpg)\n")
        bullets = read_bullets(tmp_path, dry_run=True)
        assert bullets[0]["duration"] == "auto"
        assert bullets[0]["reference_urls"] == ["https://example.com/frame.jpg"]
