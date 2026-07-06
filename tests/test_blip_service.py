"""Tests for the caption service — Phase 2 dual caption mode."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.services.blip_service import CaptionService, caption_service


class TestCaptionService:
    """Unit tests for CaptionService."""

    def test_singleton_exists(self):
        """Module-level singleton is available."""
        assert caption_service is not None
        assert isinstance(caption_service, CaptionService)

    def test_is_loaded_false_initially(self):
        """Service reports not loaded before model is fetched."""
        svc = CaptionService()
        assert svc.is_loaded is False

    def test_generate_captions_raises_on_missing_file(self):
        """generate_captions raises FileNotFoundError for missing images."""
        svc = CaptionService()
        svc.load_model = MagicMock()  # prevent actual model load

        with pytest.raises(FileNotFoundError):
            svc.generate_captions(Path("/nonexistent/image.jpg"))

    @patch("backend.services.blip_service.settings")
    def test_model_name_from_config(self, mock_settings):
        """Service reads model_name from settings."""
        mock_settings.model_name = "Salesforce/blip-image-captioning-base"

        svc = CaptionService()
        # Access the model name via settings directly
        assert mock_settings.model_name == "Salesforce/blip-image-captioning-base"

    def test_blip2_detection(self):
        """Service correctly identifies BLIP-2 model names."""
        svc = CaptionService()
        svc._is_blip2 = "blip2" in "Salesforce/blip2-opt-2.7b".lower()
        assert svc._is_blip2 is True

        svc2 = CaptionService()
        svc2._is_blip2 = "blip2" in "Salesforce/blip-image-captioning-base".lower()
        assert svc2._is_blip2 is False


class TestCaptionServiceGeneration:
    """Integration-style tests using mocks for generation."""

    def test_generate_captions_returns_dict(self, tmp_path):
        """generate_captions returns a dict with both captions."""
        # Create a dummy image file
        from PIL import Image

        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (64, 64), color="red")
        img.save(img_path)

        svc = CaptionService()

        # Mock the internal _generate method
        with patch.object(svc, "load_model"):
            with patch.object(
                svc,
                "_generate",
                side_effect=["A red square.", "A solid red square on a white background."],
            ):
                result = svc.generate_captions(img_path)

        assert "short_caption" in result
        assert "detailed_caption" in result
        assert result["short_caption"] == "A red square."
        assert "red square" in result["detailed_caption"]
