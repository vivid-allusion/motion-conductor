"""Tests for build_inputs (verbatim duration, references, Q20 warning)
and cost-estimation duration fallback (Q18)."""

import types
from pathlib import Path
from unittest.mock import patch

from src.engine_helpers import build_inputs
from src.main_verbose import _bullet_duration


class FakeInputFile:
    def __init__(self, *, path, prompt, reference_urls, metadata, references=None):
        self.path = path
        self.prompt = prompt
        self.reference_urls = reference_urls
        self.metadata = metadata
        self.references = references or {}


class OldInputFile:
    def __init__(self, *, path, prompt, reference_urls, metadata):
        self.path = path
        self.prompt = prompt
        self.reference_urls = reference_urls
        self.metadata = metadata


def _fake_module(cls):
    return types.SimpleNamespace(InputFile=cls)


def _patched_engine(cls):
    return patch(
        "src.engine_helpers.importlib.import_module",
        return_value=_fake_module(cls),
    )


def _bullet(**overrides):
    base = {
        "path": Path("a.md"),
        "prompt": "p",
        "reference_urls": [],
        "frames": None,
        "duration": None,
        "references": {},
    }
    base.update(overrides)
    return base


PROFILE = {"parameters": {"fps": 24, "duration": 5.0}}


class TestBuildInputsMetadata:
    def test_duration_integer_verbatim(self):
        with _patched_engine(FakeInputFile):
            inputs = build_inputs([_bullet(duration=5)], "replicate", profile=PROFILE)
        assert inputs[0].metadata["duration"] == 5

    def test_duration_token_verbatim(self):
        with _patched_engine(FakeInputFile):
            inputs = build_inputs(
                [_bullet(duration="auto")], "replicate", profile=PROFILE
            )
        assert inputs[0].metadata["duration"] == "auto"

    def test_duration_wins_over_frames(self):
        with _patched_engine(FakeInputFile):
            inputs = build_inputs(
                [_bullet(frames=96, duration="auto")], "replicate", profile=PROFILE
            )
        assert inputs[0].metadata["duration"] == "auto"

    def test_frames_converted_via_fps(self):
        with _patched_engine(FakeInputFile):
            inputs = build_inputs([_bullet(frames=48)], "replicate", profile=PROFILE)
        assert inputs[0].metadata["duration"] == 2.0

    def test_profile_default_when_nothing_given(self):
        with _patched_engine(FakeInputFile):
            inputs = build_inputs([_bullet()], "replicate", profile=PROFILE)
        assert inputs[0].metadata["duration"] == 5.0


class TestBuildInputsReferences:
    def test_references_passed_to_supporting_engine(self):
        bullet = _bullet(references={"reference_images": ["https://x.com/a.jpg"]})
        with _patched_engine(FakeInputFile):
            inputs = build_inputs([bullet], "replicate", profile=PROFILE)
        assert inputs[0].references == {"reference_images": ["https://x.com/a.jpg"]}

    def test_no_warning_when_engine_supports_references(self):
        with patch("src.engine_helpers.logger") as mock_logger, _patched_engine(
            FakeInputFile
        ):
            build_inputs([_bullet()], "replicate", profile=PROFILE)
        mock_logger.warning.assert_not_called()

    def test_warning_when_old_engine_drops_named_slots(self):
        bullet = _bullet(references={"reference_images": ["https://x.com/a.jpg"]})
        with patch("src.engine_helpers.logger") as mock_logger, _patched_engine(
            OldInputFile
        ):
            inputs = build_inputs([bullet], "replicate", profile=PROFILE)
        assert len(inputs) == 1
        mock_logger.warning.assert_called_once()

    def test_old_engine_without_named_refs_stays_silent(self):
        with patch("src.engine_helpers.logger") as mock_logger, _patched_engine(
            OldInputFile
        ):
            build_inputs([_bullet()], "replicate", profile=PROFILE)
        mock_logger.warning.assert_not_called()


class TestBulletDurationCost:
    def test_numeric_duration_used(self):
        assert _bullet_duration(_bullet(duration=7), PROFILE) == 7.0

    def test_token_falls_back_to_profile_default(self):
        assert _bullet_duration(_bullet(duration="auto"), PROFILE) == 5.0

    def test_negative_one_falls_back(self):
        assert _bullet_duration(_bullet(duration=-1), PROFILE) == 5.0

    def test_frames_still_converted(self):
        assert _bullet_duration(_bullet(frames=48), PROFILE) == 2.0

    def test_nothing_falls_back_to_profile_default(self):
        assert _bullet_duration(_bullet(), PROFILE) == 5.0
