"""Tests for the Confidence Gate (Grounding Service).

Verifies that the grounding mechanism correctly prevents hallucination
by only applying retrieved facts when confidence is high enough.
"""

import pytest
from unittest.mock import patch
from backend.app.services.grounding_service import GroundingService


@pytest.fixture
def grounding_service():
    """Create a GroundingService with default threshold."""
    with patch("backend.app.services.grounding_service.get_settings") as mock_settings:
        mock_settings.return_value.GROUNDING_SIMILARITY_THRESHOLD = 0.75
        yield GroundingService()


class TestConfidenceGate:
    """Test the core Confidence Gate logic."""

    def test_high_confidence_applies_grounding(self, grounding_service):
        """When similarity >= threshold, grounding is applied."""
        raw_caption = "A photo of a building"
        entries = [
            {"entity": "Taj Mahal", "fact": "Built in 1632", "score": 0.85}
        ]

        result = grounding_service.evaluate_and_ground(raw_caption, entries)

        assert result["grounding_applied"] is True
        assert "Context:" in result["final_caption"]
        assert "Built in 1632" in result["final_caption"]
        assert result["top_entity"] == "Taj Mahal"
        assert result["top_score"] == 0.85

    def test_low_confidence_skips_grounding(self, grounding_service):
        """When similarity < threshold, grounding is skipped to avoid hallucination."""
        raw_caption = "A photo of a dog"
        entries = [
            {"entity": "Taj Mahal", "fact": "Built in 1632", "score": 0.30}
        ]

        result = grounding_service.evaluate_and_ground(raw_caption, entries)

        assert result["grounding_applied"] is False
        assert result["final_caption"] == raw_caption
        assert result["top_score"] == 0.30

    def test_empty_entries_skips_grounding(self, grounding_service):
        """When no entries are retrieved, grounding is skipped."""
        raw_caption = "A photo of something"
        entries = []

        result = grounding_service.evaluate_and_ground(raw_caption, entries)

        assert result["grounding_applied"] is False
        assert result["final_caption"] == raw_caption
        assert result["top_score"] == 0.0

    def test_exact_threshold_boundary(self, grounding_service):
        """At exactly the threshold, grounding is applied (>= not >)."""
        raw_caption = "A building"
        entries = [
            {"entity": "Landmark", "fact": "Historical site", "score": 0.75}
        ]

        result = grounding_service.evaluate_and_ground(raw_caption, entries)

        assert result["grounding_applied"] is True

    def test_just_below_threshold(self, grounding_service):
        """Just below threshold, grounding is skipped."""
        raw_caption = "A building"
        entries = [
            {"entity": "Landmark", "fact": "Historical site", "score": 0.749}
        ]

        result = grounding_service.evaluate_and_ground(raw_caption, entries)

        assert result["grounding_applied"] is False

    def test_returns_metadata(self, grounding_service):
        """Grounding result includes all metadata fields."""
        raw_caption = "Test"
        entries = [
            {"entity": "Entity", "fact": "Fact", "score": 0.9}
        ]

        result = grounding_service.evaluate_and_ground(raw_caption, entries)

        assert "final_caption" in result
        assert "grounding_applied" in result
        assert "top_entity" in result
        assert "top_fact" in result
        assert "top_score" in result
        assert "threshold_used" in result
