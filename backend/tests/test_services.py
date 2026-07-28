import pytest
from unittest.mock import MagicMock, patch
from backend.app.services.grounding_service import GroundingService
from backend.app.services.translation_service import TranslationService
from backend.app.services.retrieval_service import RetrievalService

def test_grounding_high_confidence():
    service = GroundingService()
    entries = [{"score": 0.85, "entity": "Taj", "fact": "A monument"}]
    result = service.evaluate_and_ground("Raw caption.", entries)
    assert result["confidenceLabel"] == "High"
    assert result["grounding_applied"] is True

def test_grounding_reject():
    service = GroundingService()
    entries = [{"score": 0.2, "entity": "Taj", "fact": "A monument"}]
    result = service.evaluate_and_ground("Raw caption.", entries)
    assert result["confidenceLabel"] == "Reject"
    assert result["grounding_applied"] is False

@patch("backend.app.services.translation_service.get_model_manager")
def test_translation_service(mock_get):
    mock_manager = MagicMock()
    mock_bundle = {
        "tokenizer": MagicMock(),
        "model": MagicMock()
    }
    mock_bundle["tokenizer"].batch_decode.return_value = ["अनुवादित"]
    mock_manager.get_model.return_value = mock_bundle
    mock_get.return_value = mock_manager

    service = TranslationService()
    res = service.translate("Test")
    assert "hindi" in res

