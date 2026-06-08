"""Tests for domain models."""
from pathlib import Path
from src.models.generation import GenerationContext
from src.models.triplet import MarkdownJob


class TestGenerationContext:
    """Tests for GenerationContext model."""
    
    def test_creation(self):
        """Test creating a GenerationContext."""
        context = GenerationContext(
            prompt_file=Path("prompt.txt"),
            image_url_file=Path("image.txt"),
            num_frames_file=Path("frames.txt"),
            output_dir=Path("output"),
            prompt="test prompt",
            image_url="http://example.com/image.jpg",
            num_frames=100,
            profile={"name": "test"},
            params={"resolution": "480p"},
            video_url="http://example.com/video.mp4",
            video_path=Path("video.mp4"),
            cost=1.0
        )
        assert context.prompt == "test prompt"
        assert context.num_frames == 100
        assert context.cost == 1.0


class TestMarkdownJob:
    """Tests for MarkdownJob model."""
    
    def test_creation(self):
        """Test creating a MarkdownJob."""
        job = MarkdownJob(
            markdown_file=Path("test.md"),
            prompt="test prompt",
            num_frames=100,
            image_url="http://example.com/image.jpg"
        )
        assert job.prompt == "test prompt"
        assert job.num_frames == 100
        assert job.image_url == "http://example.com/image.jpg"